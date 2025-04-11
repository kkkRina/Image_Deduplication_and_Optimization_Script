import os
import hashlib
from PIL import Image
import numpy as np
from skimage.metrics import structural_similarity as ssim
import shutil

image_folder = "image_folder"  # Папка с исходными изображениями
output_folder = os.path.join(image_folder, "output")  # Папка для обработанных изображений

#Вычисляет MD5-хеш файла (для точных дубликатов)
def get_file_hash(filepath):
    with open(filepath, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

#Сравнивает изображения по SSIM с приведением к одинаковому размеру
def compare_images_ssim(img1, img2):
    img1 = img1.convert("RGB")
    img2 = img2.convert("RGB")

    width = min(img1.width, img2.width)
    height = min(img1.height, img2.height)

    img1 = img1.resize((width, height), Image.LANCZOS)
    img2 = img2.resize((width, height), Image.LANCZOS)

    img1_array = np.array(img1)
    img2_array = np.array(img2)

    try:
        score, _ = ssim(img1_array, img2_array, full=True, channel_axis=-1)
        return score
    except ValueError:
        return 0

#Находит и удаляет дубликаты в папке `output`, оставляя только одну версию
def find_and_remove_duplicates(folder):
    files = [f for f in os.listdir(folder) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
    hashes = {}  # {hash: {"path": путь, "width": ширина}}
    duplicates = 0

    for filename in files:
        filepath = os.path.join(folder, filename)
        try:
            with Image.open(filepath) as img:
                width, _ = img.size
                file_hash = get_file_hash(filepath)

                # Проверяем, есть ли уже такой хеш
                if file_hash in hashes:
                    print(f" Найден точный дубликат: {filename} (как {hashes[file_hash]['path']})")
                    os.remove(filepath)  # Удаляем дубликат
                    duplicates += 1
                    continue

                # Если хеш новый, проверяем SSIM с другими файлами
                is_duplicate = False
                for existing_hash, existing_data in hashes.items():
                    with Image.open(existing_data["path"]) as existing_img:
                        similarity = compare_images_ssim(img, existing_img)
                        if similarity > 0.95:  # Почти одинаковые изображения
                            print(f" Найден визуальный дубликат: {filename} ~ {existing_data['path']} (SSIM={similarity:.2f})")
                            # Оставляем файл с большим разрешением
                            if width > existing_data["width"]:
                                os.remove(existing_data["path"])
                                hashes[existing_hash] = {"path": filepath, "width": width}
                            else:
                                os.remove(filepath)
                            duplicates += 1
                            is_duplicate = True
                            break

                if not is_duplicate:
                    hashes[file_hash] = {"path": filepath, "width": width}
        except Exception as e:
            print(f"Ошибка при обработке {filename}: {e}")


#Обрабатывает изображения: ресайз и оптимизация
def process_images(input_folder, output_folder):
    files = [f for f in os.listdir(input_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]

    for filename in files:
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, filename)

        try:
            with Image.open(input_path) as img:
                width, height = img.size

                # Ресайз если ширина > 800px
                if width > 800:
                    new_height = int((800 / width) * height)
                    img = img.resize((800, new_height), Image.LANCZOS)
                    print(f"{filename}: изменён размер до 800px")

                # Оптимизация
                if filename.lower().endswith('.jpg') or filename.lower().endswith('.jpeg'):
                    img.save(output_path, optimize=True, quality=85)
                else:
                    img.save(output_path, optimize=True)
        except Exception as e:
            print(f"Ошибка при обработке {filename}: {e}")


print("Начало обработки...")

# Копируем изображения в папку 'output' перед удалением дубликатов
image_files = [f for f in os.listdir(image_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
for image in image_files:
    shutil.copy(os.path.join(image_folder, image), os.path.join(output_folder, image))

# Удаление дубликатов в папке 'output' (Оставляем только уникальные)
find_and_remove_duplicates(output_folder)

# Обработка изображений в папке 'output' (изменение размера и оптимизация)
process_images(output_folder, output_folder)

print("Результаты в папке 'output'")


