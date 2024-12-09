import tkinter as tk
from tkinter import messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image, ImageTk, ImageChops
import fitz  # PyMuPDF

class ImageSwitcher(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()

        self.title("Image Switcher")
        self.geometry("400x650")  # ボタンのために少し高さを追加

        # PDFファイルパスの入力用テキストボックスとラベルの作成
        self.pdf1_label = tk.Label(self, text="PDF1パス:")
        self.pdf1_label.pack(pady=5)
        self.pdf1_entry = tk.Entry(self, width=50)
        self.pdf1_entry.pack(pady=5)

        self.pdf2_label = tk.Label(self, text="PDF2パス:")
        self.pdf2_label.pack(pady=5)
        self.pdf2_entry = tk.Entry(self, width=50)
        self.pdf2_entry.pack(pady=5)

        # ドラッグ＆ドロップの設定
        self.pdf1_entry.drop_target_register(DND_FILES)
        self.pdf1_entry.dnd_bind('<<Drop>>', self.drop_pdf1)

        self.pdf2_entry.drop_target_register(DND_FILES)
        self.pdf2_entry.dnd_bind('<<Drop>>', self.drop_pdf2)

        # 停止/再開ボタンの作成
        self.control_button = tk.Button(self, text="開始", command=self.toggle_switching)
        self.control_button.pack(pady=10)

        # 次へボタンの作成
        self.next_button = tk.Button(self, text="次へ", command=self.next_page)
        self.next_button.pack(pady=10)

        # インターバル変更用テキストボックスとラベルの作成
        self.interval_label = tk.Label(self, text="インターバル (ms):")
        self.interval_label.pack(pady=5)
        self.interval_entry = tk.Entry(self)
        self.interval_entry.pack(pady=5)
        self.interval_entry.insert(0, "5000")  # 初期値を5000msに設定

        # 画像ラベルの初期設定
        self.label = tk.Label(self)
        self.label.pack()

        # 画像の切り替えと初期設定
        self.current_page = 0
        self.current_image = 1
        self.running = False  # 最初は停止状態

    def extract_images_from_pdf(self, pdf_path):
        pdf_document = fitz.open(pdf_path)
        images = []

        # 全ページから画像を抽出
        for page_number in range(len(pdf_document)):
            page = pdf_document.load_page(page_number)
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            images.append(img)

        return images

    def drop_pdf1(self, event):
        file_path = event.data
        self.pdf1_entry.delete(0, tk.END)
        self.pdf1_entry.insert(0, file_path.strip('{}'))

    def drop_pdf2(self, event):
        file_path = event.data
        self.pdf2_entry.delete(0, tk.END)
        self.pdf2_entry.insert(0, file_path.strip('{}'))

    def load_images(self):
        # テキストボックスからPDFファイルパスを取得
        self.pdf1_path = self.pdf1_entry.get()
        self.pdf2_path = self.pdf2_entry.get()

        # 各PDFの全ページから画像を抽出
        self.images_pdf1 = self.extract_images_from_pdf(self.pdf1_path)
        self.images_pdf2 = self.extract_images_from_pdf(self.pdf2_path)

        # 最初のページをリサイズ
        self.img1 = self.images_pdf1[0].resize((400, 400), Image.Resampling.LANCZOS)
        self.img2 = self.images_pdf2[0].resize((400, 400), Image.Resampling.LANCZOS)

        # PhotoImageオブジェクトの作成
        self.tk_img1 = ImageTk.PhotoImage(self.img1)
        self.tk_img2 = ImageTk.PhotoImage(self.img2)

        # 画像差異の生成
        self.diff_img = self.get_image_difference(self.img1, self.img2)
        self.tk_img_diff = ImageTk.PhotoImage(self.diff_img)

        # ラベルに最初の画像を表示
        self.label.configure(image=self.tk_img1)
        self.label.image = self.tk_img1

    def switch_image(self):
        if not self.running:
            return

        # 画像を交互に表示および差分画像を表示
        if self.current_image == 1:
            self.label.configure(image=self.tk_img2)
            self.label.image = self.tk_img2  # 参照を保持
            self.current_image = 2
        elif self.current_image == 2:
            #self.label.configure(image=self.tk_img_diff)
            #self.label.image = self.tk_img_diff  # 参照を保持
            self.current_image = 3
        else:
            self.label.configure(image=self.tk_img1)
            self.label.image = self.tk_img1  # 参照を保持
            self.current_image = 1

        # テキストボックスからインターバルを取得
        try:
            interval = int(self.interval_entry.get())
        except ValueError:
            interval = 5000  # 無効な値の場合はデフォルト値5000msを使用

        # 画像切り替えのインターバルを設定
        self.after(interval, self.switch_image)

    def get_image_difference(self, img1, img2):
        # 画像の差分を計算
        diff = ImageChops.difference(img1, img2)

        # 差分画像を強調する
        diff = diff.convert("L")
        diff = Image.eval(diff, lambda px: 255 if px > 30 else 0)
        diff = diff.convert("RGB")

        return diff

    def toggle_switching(self):
        if self.running:
            self.running = False
            self.control_button.config(text="開始", command=self.toggle_switching)
        else:
            if not hasattr(self, 'images_pdf1') or not hasattr(self, 'images_pdf2'):
                self.load_images()
            self.running = True
            self.control_button.config(text="停止", command=self.toggle_switching)
            self.switch_image()

    def next_page(self):
        self.current_page += 1

        if self.current_page < len(self.images_pdf1) and self.current_page < len(self.images_pdf2):
            self.img1 = self.images_pdf1[self.current_page].resize((400, 400), Image.Resampling.LANCZOS)
            self.img2 = self.images_pdf2[self.current_page].resize((400, 400), Image.Resampling.LANCZOS)

            # 画像差異の生成
            self.diff_img = self.get_image_difference(self.img1, self.img2)
            self.tk_img1 = ImageTk.PhotoImage(self.img1)
            self.tk_img2 = ImageTk.PhotoImage(self.img2)
            self.tk_img_diff = ImageTk.PhotoImage(self.diff_img)

            # 現在の表示画像をリセット
            self.label.configure(image=self.tk_img1)
            self.label.image = self.tk_img1  # 参照を保持
            self.current_image = 1

        else:
            self.show_completion_message()

    def show_completion_message(self): 
        self.running = False 
        self.control_button.config(state=tk.DISABLED)
        self.next_button.config(state=tk.DISABLED)
        messagebox.showinfo("終了", "終了しました")

if __name__ == "__main__":
    app = ImageSwitcher()
    app.mainloop()
