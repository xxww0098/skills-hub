#!/bin/bash

# 统一发布脚本：检测 git 变动，只同步有改动的 skill 到 skills/
# 用法:
#   bash .develop/move.sh          # 仅发布有 git 变动的 skill
#   bash .develop/move.sh --all    # 强制发布所有 skill

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SKILLS_DIR="${REPO_ROOT}/skills"
DEVELOP_REL=".develop"

# 解析参数
FORCE_ALL=false
if [ "$1" = "--all" ]; then
    FORCE_ALL=true
fi

# 获取有 git 变动的 skill 目录（含已暂存、未暂存、未追踪）
get_changed_skills() {
    cd "${REPO_ROOT}" || exit 1

    git status --porcelain -- "${DEVELOP_REL}/" 2>/dev/null \
        | awk '{print $NF}' \
        | grep "^${DEVELOP_REL}/" \
        | sed "s|^${DEVELOP_REL}/||" \
        | grep '/' \
        | cut -d'/' -f1 \
        | sort -u
}

echo "==============================="
echo "  Skills 发布"
echo "==============================="

if [ "${FORCE_ALL}" = true ]; then
    echo "  模式: 全量发布 (--all)"
    # 收集所有子目录名
    CHANGED_SKILLS=()
    for d in "${SCRIPT_DIR}"/*/; do
        [ -d "${d}" ] && CHANGED_SKILLS+=("$(basename "${d}")")
    done
else
    echo "  模式: 增量发布 (基于 git 变动)"
    # 读取 git 变动
    CHANGED_SKILLS=()
    while IFS= read -r skill; do
        [ -n "${skill}" ] && CHANGED_SKILLS+=("${skill}")
    done < <(get_changed_skills)
fi

echo ""

if [ ${#CHANGED_SKILLS[@]} -eq 0 ]; then
    echo "✨ 没有检测到变动，无需发布。"
    echo "   提示: 使用 --all 强制发布所有 skill"
    exit 0
fi

echo "检测到变动的 skill: ${CHANGED_SKILLS[*]}"
echo ""

SUCCESS_COUNT=0
SKIP_COUNT=0

for SKILL_NAME in "${CHANGED_SKILLS[@]}"; do
    SKILL_DIR="${SCRIPT_DIR}/${SKILL_NAME}"
    YAML_FILE="${SKILL_DIR}/move.yaml"

    # 跳过非目录
    if [ ! -d "${SKILL_DIR}" ]; then
        continue
    fi

    # 跳过没有 move.yaml 的目录
    if [ ! -f "${YAML_FILE}" ]; then
        echo "⏭️  ${SKILL_NAME}: 无 move.yaml，跳过"
        SKIP_COUNT=$((SKIP_COUNT + 1))
        continue
    fi

    TARGET_DIR="${SKILLS_DIR}/${SKILL_NAME}"
    mkdir -p "${TARGET_DIR}"

    # 解析 move.yaml 中的文件列表
    FILE_LIST=$(grep '^[[:space:]]*-' "${YAML_FILE}" | sed 's/^[[:space:]]*-[[:space:]]*//' | sed "s/['\"]//g")

    # 处理空列表
    if [ -z "${FILE_LIST}" ]; then
        echo "⏭️  ${SKILL_NAME}: 无需同步的文件"
        SKIP_COUNT=$((SKIP_COUNT + 1))
        continue
    fi

    echo "📦 ${SKILL_NAME}:"

    echo "${FILE_LIST}" | while read -r file; do
        [ -z "${file}" ] && continue

        BASENAME=$(basename "${file}")
        SOURCE_PATH="${SKILL_DIR}/${BASENAME}"

        if [ -e "${SOURCE_PATH}" ]; then
            [ -e "${TARGET_DIR}/${BASENAME}" ] && rm -rf "${TARGET_DIR}/${BASENAME}"
            cp -R "${SOURCE_PATH}" "${TARGET_DIR}/"
            echo "   ✅ ${BASENAME}"
        else
            echo "   ⚠️  找不到 ${BASENAME}，跳过"
        fi
    done

    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    echo ""
done

echo "==============================="
echo "  完成: ✅ ${SUCCESS_COUNT} 发布 | ⏭️ ${SKIP_COUNT} 跳过"
echo "==============================="
