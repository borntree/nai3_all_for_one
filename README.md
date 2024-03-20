#  nai3_all_for_one

此项目改写自
https://github.com/wochenlong/nai3_train
因为本人自用原因，只保留了“随机角色(或者说前置tag)+固定tag+随机末尾tag”的组合，改写自[random_characetrs_expression.py](https://github.com/wochenlong/nai3_train/blob/main/random_characetrs_expression.py)

原理1&2内的设置及相关运行配置请参阅
https://github.com/wochenlong/nai3_train/blob/main/README.md

如果你需要使用nai3生成指定(随机角色(或者说前置tag)+固定tag+随机末尾tag)数量的图片，并将一定数量的图像拼合为一个大图，然后将这些图片全部加上水印再整理到一个文件夹内，那么你需要这个项目

原理1：从1_character读取json作为前置tag，从2_prompt读取固定tag，从3_append_prompt读取末尾tag，结合到一起批量生成随机素材，放入4_generate_output文件夹

原理2：从json中随机/按顺序抽取前置tag，随机抽取末尾tag

原理3：all_for_one.py每次出图结束会检测4_generate_output文件夹内的图片数量，达到指定的9张执行以下程序(采用os.system+休眠来控制程序执行间隔，电脑配置过低请调高image_processing()内的休眠时间)：
  1.启动9imgs.py来拼合这9张图，输出到5_joint_output文件夹
  2.分别启动marker.py和marker9.py来对9张图片和拼合图片打水印，输出到6_marker文件夹
  3.在7_pack内新建文件夹，并将这总计20张图移动至此

备注(重要)：
1.运行脚本前请先在项目文件"token.txt"内填入自己的nai3账号token
  获取方法1：
  在网页（https://novelai.net） 中登录你的 NovelAI 账号
    - 打开控制台 (F12)，并切换到控制台 (Console) 标签页
    - 输入下面的代码并按下回车运行：
      ```javascript
      console.log(JSON.parse(localStorage.session).auth_token)
      ```
    - 输出的字符串就是你的授权令牌
  
  获取方法2：
  ![Image](https://github.com/users/borntree/projects/1/assets/82987943/f66b25b8-a298-43fc-9c09-0f19287e6ae6)

2.下次运行脚本前请清空7_pack文件夹内的文件，否则可能发生意外

3.因为本人是做头像的，因此大图片拼合都是1024*1024，其他尺寸并未研究，不过只是出图不拼合的话并不影响(建议直接用[nai3_train](https://github.com/wochenlong/nai3_train
))。

## 安装运行环境

```bash
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

## 运行
`python nai3_all_for_one.py`

## 图片拼合
```javascript
IMAGES_PATH = r'.\4_generate_output\\'  # 图片集地址
IMAGES_FORMAT = ['.png', '.PNG']  # 图片格式，nai3默认保存格式
IMAGE_SIZE = 1024  # 每张小图片的大小
IMAGE_ROW = 3  # 图片间隔，也就是合并成一张图后，一共有几行
IMAGE_COLUMN = 3  # 图片间隔，也就是合并成一张图后，一共有几列，之所以叫9imges就是因为3*3=9，可以自己设定，但要随之更改all_for_one里面出图循环的判定数值if generator.generate_files_num() == 9:
IMAGE_SAVE_PATH = r'.\5_joint_output\0.png'  # 图片转换后的地址
```

## 水印
help的内容我懒得改了，水印的位置受字体大小&间距&倾斜角度的影响，为了大图和小图主体不受影响，调了很久的参数，因此有2个打水印的py文件
```javascript
    parse = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parse.add_argument("-f", "--file", type=str, default="./4_generate_output", #读取图片的位置
                       help="image file path or directory")
    parse.add_argument("-m", "--mark", type=str, default="我是水印", help="watermark content") #default水印内容
    parse.add_argument("-o", "--out", default="./6_marker", #输出位置
                       help="image output directory, default is ./output")
    parse.add_argument("-c", "--color", default="#363433", type=str, #字体颜色
                       help="text color like '#363433', default is #fbc82f")
    parse.add_argument("-s", "--space", default=900, type=int, #字体大小
                       help="space between watermarks, default is 75")
    parse.add_argument("-a", "--angle", default=0, type=int, #倾斜角度
                       help="rotate angle of watermarks, default is 30")
    parse.add_argument("--font-family", default="./font/Inkfree.ttf", type=str, #字体读取，可以自己找好看字体
                       help=textwrap.dedent('''\
                       font family of text, default is './font/Inkfree.ttf'
                       using font in system just by font file name
                       for example 'PingFang.ttc', which is default installed on macOS
                       '''))
    parse.add_argument("--font-height-crop", default="1.2", type=str, #字体间距
                       help=textwrap.dedent('''\
                       change watermark font height crop
                       float will be parsed to factor; int will be parsed to value
                       default is '1.2', meaning 1.2 times font size
                       this useful with CJK font, because line height may be higher than size
                       '''))
    parse.add_argument("--size", default=125, type=int, #字体大小
                       help="font size of text, default is 50")
    parse.add_argument("--opacity", default=0.5, type=float, #透明度
                       help="opacity of watermarks, default is 0.15")
    parse.add_argument("--quality", default=300, type=int, #质量
                       help="quality of output images, default is 80")
```