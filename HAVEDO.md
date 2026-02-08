创建GitHub仓库
克隆仓库到本地进行开发 
```code 
git clone https://github.com/choril/ResGenie.git
```
创建Python版本文件
```code
echo "3.10.12" > .python-version
```
创建uv环境
```code
uv venv --python 3.10.12
```
创建项目结构
```code
mkdir -p src/{agents,api,core,services,models,utils,workers}
mkdir -p tests/{unit,integration}
mkdir -p frontend/{public,src}
mkdir -p docs config data/{cache,vector_store}
```
