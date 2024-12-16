import tkinter as tk
from tkinter import messagebox, Toplevel
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image, ImageTk, ImageChops
import fitz  # PyMuPDF

class ImageSwitcher(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()

        self.title("Image Switcher")
        self.geometry("500x150")  # ウィンドウサイズを大きく設定

        # PDFファイルパスの入力用テキストボックスとラベルの作成
        self.pdf1_label = tk.Label(self, text="PDF1パス:")
        self.pdf1_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.pdf1_entry = tk.Entry(self, width=50)
        self.pdf1_entry.grid(row=0, column=1, padx=5, pady=5)

        self.pdf2_label = tk.Label(self, text="PDF2パス:")
        self.pdf2_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.pdf2_entry = tk.Entry(self, width=50)
        self.pdf2_entry.grid(row=1, column=1, padx=5, pady=5)

        # ドラッグ＆ドロップの設定
        self.pdf1_entry.drop_target_register(DND_FILES)
        self.pdf1_entry.dnd_bind('<<Drop>>', self.drop_pdf1)

        self.pdf2_entry.drop_target_register(DND_FILES)
        self.pdf2_entry.dnd_bind('<<Drop>>', self.drop_pdf2)

        # インターバル変更用テキストボックスとラベルの作成
        self.interval_label = tk.Label(self, text="インターバル (ms):")
        self.interval_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.interval_entry = tk.Entry(self)
        self.interval_entry.grid(row=2, column=1, padx=5, pady=5)
        self.interval_entry.insert(0, "500")  # 初期値を500msに設定

        # 停止/再開ボタンと次へボタンの作成
        self.button_frame = tk.Frame(self)
        self.button_frame.grid(row=3, column=0, columnspan=2, pady=10)

        self.control_button = tk.Button(self.button_frame, text="開始", command=self.toggle_switching)
        self.control_button.pack(side=tk.LEFT, padx=5)

        self.next_button = tk.Button(self.button_frame, text="次へ", command=self.next_page)
        self.next_button.pack(side=tk.LEFT, padx=5)

        # 拡大ボタンと縮小ボタンの作成
        self.zoom_in_button = tk.Button(self.button_frame, text="拡大", command=self.zoom_in)
        self.zoom_in_button.pack(side=tk.LEFT, padx=5)

        self.zoom_out_button = tk.Button(self.button_frame, text="縮小", command=self.zoom_out)
        self.zoom_out_button.pack(side=tk.LEFT, padx=5)

        # 画像の切り替えと初期設定
        self.current_page = 0
        self.current_image = 1
        self.running = False  # 最初は停止状態
        self.image_window = None  # 新しいウィンドウの参照を保持
        self.img1 = None  # 現在表示されている画像1の参照を保持
        self.img2 = None  # 現在表示されている画像2の参照を保持

        # キーイベントのバインド
        self.bind("<KeyPress-1>", self.show_image1)
        self.bind("<KeyPress-2>", self.show_image2)
        self.bind("<KeyPress-3>", self.show_diff_image1)
        self.bind("<KeyPress-4>", self.show_diff_image2)

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

        # PDFファイルが正しく読み込まれたか確認
        if not self.images_pdf1 or not self.images_pdf2:
            messagebox.showerror("エラー", "PDFファイルの読み込みに失敗しました。")
            return

        # 最初のページをリサイズして表示
        self.img1 = self.resize_image(self.images_pdf1[0])
        self.img2 = self.resize_image(self.images_pdf2[0])

        # PhotoImageオブジェクトの作成
        self.tk_img1 = ImageTk.PhotoImage(self.img1)
        self.tk_img2 = ImageTk.PhotoImage(self.img2)

        # 画像差異の生成
        self.diff_img1_to_2, self.diff_img2_to_1 = self.get_image_differences(self.img1, self.img2)
        self.tk_img_diff1_to_2 = ImageTk.PhotoImage(self.diff_img1_to_2)
        self.tk_img_diff2_to_1 = ImageTk.PhotoImage(self.diff_img2_to_1)

    def resize_image(self, img):
        # 画像の比率を維持しながらリサイズ
        max_width, max_height = 800, 800
        img_ratio = img.width / img.height
        if img.width > max_width or img.height > max_height:
            if img_ratio > 1:
                new_width = max_width
                new_height = int(max_width / img_ratio)
            else:
                new_height = max_height
                new_width = int(max_height * img_ratio)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        return img

    def switch_image(self):
        if not self.running:
            return

        # 画像を交互に表示および差分画像を表示
        if self.current_image == 1:
            self.show_image(self.tk_img2, self.img2)
            self.current_image = 2
        elif self.current_image == 2:
            self.show_image(self.tk_img_diff1_to_2, self.diff_img1_to_2)
            self.current_image = 3
        elif self.current_image == 3:
            self.show_image(self.tk_img_diff2_to_1, self.diff_img2_to_1)
            self.current_image = 4
        else:
            self.show_image(self.tk_img1, self.img1)
            self.current_image = 1

        # テキストボックスからインターバルを取得
        try:
            interval = int(self.interval_entry.get())
        except ValueError:
            interval = 5000  # 無効な値の場合はデフォルト値5000msを使用

        # 画像切り替えのインターバルを設定
        self.after(interval, self.switch_image)

    def show_image(self, tk_img, img):
        if self.image_window is None or not self.image_window.winfo_exists():
            self.image_window = Toplevel(self)
            self.image_window.title("Image Display")
            self.image_window.geometry("800x800")
            self.image_window.protocol("WM_DELETE_WINDOW", self.on_image_window_close)
            self.image_label = tk.Label(self.image_window)
            self.image_label.pack()

            # キーイベントのバインド
            self.image_window.bind("<KeyPress-1>", self.show_image1)
            self.image_window.bind("<KeyPress-2>", self.show_image2)
            self.image_window.bind("<KeyPress-3>", self.show_diff_image1)
            self.image_window.bind("<KeyPress-4>", self.show_diff_image2)

        self.image_label.configure(image=tk_img)
        self.image_label.image = tk_img
        self.img = img  # 現在表示されている画像の参照を更新

    def show_image1(self, event):
        self.show_image(self.tk_img1, self.img1)

    def show_image2(self, event):
        self.show_image(self.tk_img2, self.img2)

    def show_diff_image1(self, event):
        self.show_image(self.tk_img_diff1_to_2, self.diff_img1_to_2)

    def show_diff_image2(self, event):
        self.show_image(self.tk_img_diff2_to_1, self.diff_img2_to_1)

    def zoom_in(self):
        # 画像を拡大
        self.img1 = self.img1.resize((int(self.img1.width * 1.2), int(self.img1.height * 1.2)), Image.Resampling.LANCZOS)
        self.img2 = self.img2.resize((int(self.img2.width * 1.2), int(self.img2.height * 1.2)), Image.Resampling.LANCZOS)
        self.diff_img1_to_2, self.diff_img2_to_1 = self.get_image_differences(self.img1, self.img2)

        self.tk_img1 = ImageTk.PhotoImage(self.img1)
        self.tk_img2 = ImageTk.PhotoImage(self.img2)
        self.tk_img_diff1_to_2 = ImageTk.PhotoImage(self.diff_img1_to_2)
        self.tk_img_diff2_to_1 = ImageTk.PhotoImage(self.diff_img2_to_1)

        # 現在表示されている画像を更新
        if self.current_image == 1:
            self.image_label.configure(image=self.tk_img1)
            self.image_label.image = self.tk_img1
        elif self.current_image == 2:
            self.image_label.configure(image=self.tk_img2)
            self.image_label.image = self.tk_img2
        elif self.current_image == 3:
            self.image_label.configure(image=self.tk_img_diff1_to_2)
            self.image_label.image = self.tk_img_diff1_to_2
        else:
            self.image_label.configure(image=self.tk_img_diff2_to_1)
            self.image_label.image = self.tk_img_diff2_to_1

    def zoom_out(self):
        # 画像を縮小
        self.img1 = self.img1.resize((int(self.img1.width * 0.8), int(self.img1.height * 0.8)), Image.Resampling.LANCZOS)
        self.img2 = self.img2.resize((int(self.img2.width * 0.8), int(self.img2.height * 0.8)), Image.Resampling.LANCZOS)
        self.diff_img1_to_2, self.diff_img2_to_1 = self.get_image_differences(self.img1, self.img2)

        self.tk_img1 = ImageTk.PhotoImage(self.img1)
        self.tk_img2 = ImageTk.PhotoImage(self.img2)
        self.tk_img_diff1_to_2 = ImageTk.PhotoImage(self.diff_img1_to_2)
        self.tk_img_diff2_to_1 = ImageTk.PhotoImage(self.diff_img2_to_1)

        # 現在表示されている画像を更新
        if self.current_image == 1:
            self.image_label.configure(image=self.tk_img1)
            self.image_label.image = self.tk_img1
        elif self.current_image == 2:
            self.image_label.configure(image=self.tk_img2)
            self.image_label.image = self.tk_img2
        elif self.current_image == 3:
            self.image_label.configure(image=self.tk_img_diff1_to_2)
            self.image_label.image = self.tk_img_diff1_to_2
        else:
            self.image_label.configure(image=self.tk_img_diff2_to_1)
            self.image_label.image = self.tk_img_diff2_to_1

    def on_image_window_close(self):
        self.running = False
        self.control_button.config(text="開始", command=self.toggle_switching)
        self.image_window.destroy()

    def get_image_difference(self, img1, img2):
        # 画像の差分を計算
        diff = ImageChops.difference(img1, img2)

        # 差分画像を強調する
        diff = diff.convert("L")
        diff = Image.eval(diff, lambda px: 255 if px > 30 else 0)
        diff = diff.convert("RGB")

        return diff

    def get_image_differences(self, img1, img2):
        # 画像の差分を計算
        diff1 = ImageChops.difference(img1, img2)
        diff2 = ImageChops.difference(img2, img1)

        # 差分画像を強調する
        diff1 = diff1.convert("L")
        #diff1 = Image.eval(diff1, lambda px: 255 if px > 30 else 0)
        diff1 = Image.eval(diff1, lambda px: 0 if px > 30 else 255)
        diff1 = diff1.convert("RGB")

        diff2 = diff2.convert("L")
        #diff2 = Image.eval(diff2, lambda px: 255 if px > 30 else 0)
        diff2 = Image.eval(diff2, lambda px: 0 if px > 30 else 255)
        diff2 = diff2.convert("RGB")

        diff_img1 = Image.blend(img1, diff1, alpha=0.5)
        diff_img2 = Image.blend(img2, diff2, alpha=0.5)

        return diff_img1, diff_img2

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
        messagebox.showinfo(self.current_page, self.current_page)
        if self.current_page < len(self.images_pdf1) and self.current_page < len(self.images_pdf2):
            self.img1 = self.resize_image(self.images_pdf1[self.current_page])
            self.img2 = self.resize_image(self.images_pdf2[self.current_page])

            self.tk_img1 = ImageTk.PhotoImage(self.img1)
            self.tk_img2 = ImageTk.PhotoImage(self.img2)

            # 画像差異の生成
            self.diff_img1_to_2, self.diff_img2_to_1 = self.get_image_differences(self.img1, self.img2)
            self.tk_img_diff1_to_2 = ImageTk.PhotoImage(self.diff_img1_to_2)
            self.tk_img_diff2_to_1 = ImageTk.PhotoImage(self.diff_img2_to_1)

            # 現在の表示画像をリセット
            self.show_image(self.tk_img1, self.img1)
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
