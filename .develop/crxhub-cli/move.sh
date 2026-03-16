#!/bin/bash

# 获取脚本所在目录，确保相对路径正确
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

# 动态获取当前文件夹名称（如 crxhub）作为技能包名
SKILL_NAME="$(basename "${SCRIPT_DIR}")"

# 目标目录: 自动指向 skills 目录下的同名文件夹
TARGET_DIR="${SCRIPT_DIR}/../../skills/${SKILL_NAME}"
YAML_FILE="${SCRIPT_DIR}/move.yaml"

echo "=== 开始迁移 ==="

# 1. 迁移前，如果有目标文件夹，强制删除
if [ -d "${TARGET_DIR}" ]; then
    echo "发现已存在的目标目录 ${TARGET_DIR}，正在强制删除..."
    rm -rf "${TARGET_DIR}"
fi

# 2. 自动创建目标文件夹
echo "创建目标目录 ${TARGET_DIR}..."
mkdir -p "${TARGET_DIR}"

# 3. 读取 move.yaml 并迁移文件
echo "读取迁移列表 ${YAML_FILE}..."

# 校验 yaml 文件是否存在
if [ ! -f "${YAML_FILE}" ]; then
    echo "错误：未找到 ${YAML_FILE}"
    exit 1
fi

# 解析 move.yaml：抓取 "-" 开头的行，并去除多余字符
grep '^[[:space:]]*-' "${YAML_FILE}" | sed 's/^[[:space:]]*-[[:space:]]*//' | sed "s/['\"]//g" | while read -r file; do
    if [ -z "${file}" ]; then
        continue
    fi
    
    # 获取真正的基础文件名（如果 yaml 里写的是带路径的）
    BASENAME=$(basename "${file}")
    SOURCE_PATH="${SCRIPT_DIR}/${BASENAME}"
    
    if [ -e "${SOURCE_PATH}" ]; then
        echo "迁移文件/目录: ${BASENAME}"
        cp -R "${SOURCE_PATH}" "${TARGET_DIR}/"
    else
        echo "警告: 找不到 ${SOURCE_PATH}，跳过该项。"
    fi
done

echo "=== 迁移完成 ==="
