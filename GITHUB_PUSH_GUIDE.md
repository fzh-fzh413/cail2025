# 📤 将代码推送到 GitHub 完整指南

本指南将帮助您将项目代码推送到 GitHub，以便在 Render 等平台上部署。

## 📋 前置准备

1. **安装 Git**
   - 下载地址：https://git-scm.com/download/win
   - 安装时保持默认选项即可
   - 安装完成后，在 PowerShell 中验证：
     ```bash
     git --version
     ```

2. **注册 GitHub 账号**
   - 访问：https://github.com
   - 如果没有账号，点击 "Sign up" 注册

## 🚀 推送步骤

### 步骤 1：初始化 Git 仓库

在项目根目录（`pythonProject1`）打开 PowerShell，执行：

```bash
# 进入项目目录（如果还没有）
cd C:\Users\fzh\Desktop\pythonProject1

# 初始化 Git 仓库
git init
```

### 步骤 2：配置 Git（首次使用需要）

```bash
# 设置用户名（替换为您的 GitHub 用户名）
git config --global user.name "Your Name"

# 设置邮箱（替换为您的 GitHub 邮箱）
git config --global user.email "your.email@example.com"
```

### 步骤 3：添加文件到暂存区

```bash
# 查看当前状态
git status

# 添加所有文件（.gitignore 会自动排除不需要的文件）
git add .
```

### 步骤 4：提交代码

```bash
# 创建第一次提交
git commit -m "Initial commit: Ready for Render deployment"
```

### 步骤 5：在 GitHub 上创建仓库

1. 登录 https://github.com
2. 点击右上角的 **"+"** 图标
3. 选择 **"New repository"**
4. 填写仓库信息：
   - **Repository name**: 输入仓库名称（如：`legal-ai-api`）
   - **Description**: 可选，输入项目描述
   - **Visibility**: 选择 Public（公开）或 Private（私有）
   - ⚠️ **不要勾选** "Add a README file"、"Add .gitignore"、"Choose a license"
5. 点击 **"Create repository"**

### 步骤 6：连接本地仓库到 GitHub

在 PowerShell 中执行（将 `YOUR_USERNAME` 和 `YOUR_REPO_NAME` 替换为实际值）：

```bash
# 添加远程仓库
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# 例如：
# git remote add origin https://github.com/zhangfan/legal-ai-api.git
```

### 步骤 7：推送到 GitHub

```bash
# 将分支重命名为 main（GitHub 默认使用 main）
git branch -M main

# 推送到 GitHub
git push -u origin main
```

**注意**：首次推送时，GitHub 可能会要求您输入用户名和密码：
- **用户名**：您的 GitHub 用户名
- **密码**：需要使用 **Personal Access Token**（不是 GitHub 密码）

### 步骤 8：创建 Personal Access Token（如果需要）

如果推送时提示需要密码，请按以下步骤创建 Token：

1. 登录 GitHub，点击右上角头像 → **Settings**
2. 左侧菜单选择 **Developer settings**
3. 选择 **Personal access tokens** → **Tokens (classic)**
4. 点击 **Generate new token** → **Generate new token (classic)**
5. 填写信息：
   - **Note**: 输入描述（如：Render Deployment）
   - **Expiration**: 选择过期时间
   - **Select scopes**: 勾选 **repo**（完整仓库权限）
6. 点击 **Generate token**
7. **复制生成的 token**（只显示一次，请保存好）
8. 在推送时，密码处粘贴这个 token

## ✅ 验证推送成功

1. 刷新 GitHub 网页，您应该能看到所有文件
2. 或者执行以下命令查看远程仓库：
   ```bash
   git remote -v
   ```

## 🔄 后续更新代码

当您修改代码后，使用以下命令更新 GitHub：

```bash
# 1. 查看修改的文件
git status

# 2. 添加修改的文件
git add .

# 3. 提交修改
git commit -m "描述您的修改内容"

# 4. 推送到 GitHub
git push
```

## 🐛 常见问题

### Q1: 推送时提示 "remote origin already exists"
**解决方案**：
```bash
# 删除现有的远程仓库
git remote remove origin

# 重新添加
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
```

### Q2: 推送时提示 "failed to push some refs"
**解决方案**：
```bash
# 先拉取远程代码（如果有 README 等文件）
git pull origin main --allow-unrelated-histories

# 解决冲突后再次推送
git push -u origin main
```

### Q3: 忘记密码/Token
**解决方案**：
- 在 Windows 中，打开 **控制面板** → **凭据管理器** → **Windows 凭据**
- 找到 `git:https://github.com`，删除它
- 重新推送时会要求重新输入

### Q4: 想排除某些文件
**解决方案**：
- 编辑 `.gitignore` 文件，添加要排除的文件或文件夹
- 例如：`*.log`、`temp/` 等

## 📝 下一步

代码推送到 GitHub 后，您可以：

1. **在 Render 中部署**：
   - 参考 `快速部署选择.md` 中的步骤 3.2
   - Render 会自动检测 GitHub 仓库的更新并重新部署

2. **查看代码**：
   - 在 GitHub 网页上浏览您的代码
   - 分享仓库链接给他人

3. **协作开发**：
   - 邀请团队成员加入仓库
   - 使用 Issues 和 Pull Requests 管理项目

---

**提示**：如果遇到任何问题，可以查看 Git 官方文档：https://git-scm.com/doc

