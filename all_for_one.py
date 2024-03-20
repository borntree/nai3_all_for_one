import random
import shutil
import requests
import zipfile
import os
import json
import string
import time
import zipfile
import io
import subprocess
from requests.exceptions import SSLError, RequestException

# 用户自定义 角色 JSON 文件的路径
characters_path = r"./1_character/genshin_poimiku.json"
# 用户自定义 尾部关键词 JSON 文件的路径
append_prompt_path = r"./3_append_prompt/append_prompt.json"
# 生成图像文件的保存路径
folder_path = "./4_generate_output"
# 选择读取方式(仅限角色，尾部关键词为随机读取)
read_mode = -1  # -1为随机读取，1为按顺序读取

# 设置角色优先级
role_priority = 1  # 默认为0时不生效,选择1时，把角色词优先放prompt 前面

# 选择 seed
seed = -1  # 默认随机 seed，默认随机 seed，不填或者设置为-1时为随机seed

token = None  # 目录创建一个token.txt文件夹，将你的token粘贴进去
with open("./token.txt", "r") as file:
    token = file.read()

with open(r"./2_prompt/prompt.txt", "r") as file: # 读取文本文件内容作为 反向prompt 参数的值
    prefix = file.read()

with open(r"./2_prompt/negative_prompt.txt", "r") as file: # 读取文本文件内容作为 反向prompt 参数的值
    negative_prompt = file.read()

# 生成多张图像并保存
num_images = 15  # 要生成的图像数量(出图会有失败，实际出图为此数量左右，必为9的倍数)
batch_size = 10  # 每批次生成的图像数量
retry_delay = 20  # 每批次生成后的休眠时间（单位：秒）

# 生成文件数量检测
generate_num = 0 #第x次生成文件
# 真批次
global batch
batch = 0

# 图像处理
def image_processing():
    os.system('python 9imgs.py') # 图片拼合
    time.sleep(5)
    os.system('python marker.py') # 小图片添加水印
    time.sleep(9)
    os.system('python marker9.py') # 大图片添加水印
    time.sleep(9)

# 文件转移
def remove_file(old_path, new_path):
    filelist = os.listdir(old_path)      #列出该目录下的所有文件,listdir返回的文件列表是不包含路径的。
    print(filelist)
    for file in filelist:
        src = os.path.join(old_path, file)
        dst = os.path.join(new_path, file)
        shutil.move(src, dst)

# 所有文件转移至新文件夹
def move_all():
    last_path = f"./7_pack/{batch}"
    os.makedirs(last_path)
    remove_file("./4_generate_output", last_path)
    remove_file("./5_joint_output", last_path)
    remove_file("./6_marker", last_path)

sleep_time_batch_min = 1  # 每批次生成后的休眠时间最小值（单位：秒）
sleep_time_batch_max = 3  # 每批次生成后的休眠时间最小值（单位：秒）
sleep_time_single_min = 0.5  # 每张图生成后的休眠时间最小值（单位：秒）
sleep_time_single_max = 3  # 每张图生成后的休眠时间最小值（单位：秒）

retry_delay = 1  # 因为报错中断，脚本的重新启动时间（单位：秒）

class NovelaiImageGenerator:
    def __init__(self, characters_path, negative_prompt, append_prompt_path):
        self.token = token
        self.api = "https://api.novelai.net/ai/generate-image"
        self.headers = {
            "authorization": f"Bearer {self.token}",
            "referer": "https://novelai.net",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36",
        }
        self.json = {
            "input": "",
            "model": "nai-diffusion-3",
            "action": "generate",
            "parameters": {
                "width": 1024,
                "height": 1024,
                "scale": 5,
                "sampler": "k_euler",
                "steps": 28,
                "seed": 0,
                "n_samples": 1,
                "ucPreset": 0,
                "qualityToggle": "true",
                "sm": "true",
                "sm_dyn": "false",
                "dynamic_thresholding": "false",
                "controlnet_strength": 1,
                "legacy": "false",
                "add_original_image": "false",
                "uncond_scale": 1,
                "cfg_rescale": 0,
                "noise_schedule": "native",
                "negative_prompt": negative_prompt,
            },
        }

        self.characters_path = characters_path
        self.characters = []
        self.current_character_index = 0

        self.append_prompt_path = append_prompt_path
        self.append_prompt = []

    def load_characters(self):          # 加载角色文件
        with open(self.characters_path, "r") as file:
            data = json.load(file)
            self.characters = data["role"]

    def get_random_character(self):     # 获取随机角色文本
        return random.choice(self.characters)

    def get_next_character(self):       #获取下一角色文本
        character = self.characters[self.current_character_index]
        self.current_character_index = (self.current_character_index + 1) % len(
            self.characters
        )
        return character

    def load_append_prompt(self):          # 加载尾部关键词文件
        with open(self.append_prompt_path, "r") as file:
            data = json.load(file)
            self.append_prompt = data["append_prompt"]

    def get_random_append_prompt(self):     # 获取随机尾部关键词文本
        return random.choice(self.append_prompt)


    def generate_image(self, prefix, random_mode=True, seed=None):
        if seed is None or seed == -1:
            seed = random.randint(0, 9999999999)
        self.json["parameters"]["seed"] = seed

        random_append_prompt = self.get_random_append_prompt()

        if random_mode:
            random_character = self.get_random_character()
        else:
            random_character = self.get_next_character()

        if role_priority == 1:
            random_character = self.get_random_character()
            self.json["input"] = random_character + prefix + random_append_prompt
        else:
            self.json["input"] = prefix + random_character + random_append_prompt

        r = requests.post(
            self.api, json=self.json, headers=self.headers
        )  # 将这行移动到这里，确保任何情况下都会执行
        with zipfile.ZipFile(io.BytesIO(r.content), mode="r") as zip:
            with zip.open("image_0.png") as image:
                return image.read()

    def generate_files_num(self):
        return len(os.listdir("./4_generate_output")) #检测文件夹内图片数量

def save_image_from_binary(image_data, folder_path):
    file_name = f"{generate_num}"
    file_path = os.path.join(folder_path, file_name + ".png")

    try:
        with open(file_path, "wb") as file:
            file.write(image_data)
        print("图像已保存到：", file_path)
    except IOError as e:
        print("保存图像时出错：", e)


generator = NovelaiImageGenerator(
    characters_path=characters_path, negative_prompt=negative_prompt, append_prompt_path=append_prompt_path
)

# 加载角色列表
generator.load_characters()
#加载尾部关键词列表
generator.load_append_prompt()


# 判断读取方式
if read_mode == -1:
    random_mode = True
else:
    random_mode = False

# 生成并保存图像
image_data = generator.generate_image("prefix_", random_mode=random_mode)
save_image_from_binary(image_data, "image_folder")


while 1:
    if generate_num > num_images and generator.generate_files_num() == 0:
        break
    else:
        generate_num = generate_num + 1
        try:
            # 生成图像数据
            image_data = generator.generate_image(prefix)
            if image_data is None:
                continue

            # 保存图像文件
            save_image_from_binary(image_data, folder_path)
            print(f"当前4_generate_output图像数量为:{generator.generate_files_num()}")
            if generator.generate_files_num() == 9:
                image_processing()
                batch = batch + 1
                print(f"第{batch}批处理中")
                move_all()
                time.sleep(5)
                print(f"第{batch}批处理完成")
            if (generate_num + 1) % batch_size == 0:  # 批次执行结束休眠
                sleep_time = (
                    random.uniform(sleep_time_batch_min * 100, sleep_time_batch_max * 100)
                    / 100.0
                )
                print(f"已生成 {generate_num + 1} 张图像，休眠 {sleep_time} 秒...")
                time.sleep(sleep_time)
            else:  # 单次执行完后休眠
                sleep_time = (
                    random.uniform(sleep_time_single_min * 100, sleep_time_single_max * 100)
                    / 100.0
                )
                print(f"图像生成完毕，休眠 {sleep_time} 秒...")
                time.sleep(sleep_time)
        except (SSLError, RequestException) as e:
            print("发生错误:", e)
            print(f"休眠 {retry_delay} 秒后重新启动")
        except zipfile.BadZipFile as e:
            print("发生错误:", e)
            print("忽略此错误，继续脚本运行")
