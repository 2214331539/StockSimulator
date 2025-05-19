### 1、克隆远程仓库到本地

- **在 GitHub 上找到你要协作的仓库。**

- **点击仓库页面上的 "Code" 按钮。**

- **复制仓库的 URL。** 选择使用 HTTPS 

- **打开你的终端（Terminal 或 Command Prompt）。**

- **导航到你想要将仓库克隆到的本地目录。** 使用 `cd` 命令。

- **运行 `git clone` 命令，后面跟上你复制的仓库 URL：**

```bash
git clone <仓库 URL>

# 例如 HTTPS: git clone https://github.com/组织或用户名/仓库名.git

```

### 2、在代码根目录文件夹下打开git bash

因为要修改原始代码，我们需要保持原始代码不变的情况下创建一个新的分支，修改完成后再将新分支的代码同步到主分支上。

因此我们接下来创建一个新的本地分支

```bash
git checkout -b <分支名称>
# 例如gitcheckout -b solve_login
```

### 3、进行本地修改和提交

接下来就可以在代码文件里进行coding操作

代码修改完以后再次在根目录下打开git，依次执行以下步骤

```bash
#添加所有更改的文件
git add .

#提交更改
git commit -m "更改的信息，尽可能完整清晰"
```



### 4、推送本地代码到远程仓库

```bash
git push -u origin <你的分支名称>
```



### 5、创建Pull Request来合并修改

一旦你的本地分支被成功推送到远程仓库，你就可以在 GitHub 上创建一个 Pull Request，请求将你的更改合并到主分支。

1. **在 GitHub 上导航到你克隆的仓库。**
2. **你应该会看到一个提示，询问你是否要为你的新推送的分支创建一个 Pull Request。** 点击 "Compare & pull request" 按钮。
3. **如果提示没有自动出现，你可以点击仓库页面上的 "Pull requests" 选项卡，然后点击 "New pull request" 按钮。**
4. **在创建 Pull Request 的页面上：**
   - **Base repository:** 选择你想要将你的更改合并到的目标仓库（通常是原始仓库）。
   - **Base:** 选择你想要将你的更改合并到的目标分支（通常是 `main` 或 `master`）。
   - **Compare:** 选择你刚刚推送的包含你的更改的分支（`<你的分支名称>`）。

### 6 更新本地主分支

1、切换到本地主分支

```bash
git checkout main
```

2、拉取远程主分支的最新更改

```
git pull origin main
```

3、删除刚刚修改代码创建的新分支

```bash
git branch -d <你的分支名称>
```

