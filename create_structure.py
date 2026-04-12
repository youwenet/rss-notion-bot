import os

# 所有需要创建的文件夹
folders = [
    "frontend/assets/css",
    "frontend/assets/js",
    "frontend/assets/images",

    "core/db1_paper",
    "core/db2_model",
    "core/db3_case",
    "core/db4_script",

    "workflow",

    "assets",
    "publish",

    "outputs/temp_images",
    "outputs/logs"
]

# 自动创建
for folder in folders:
    os.makedirs(folder, exist_ok=True)
    print(f"✅ 创建完成: {folder}")

print("\n🎉 所有文件夹一键创建完毕！")