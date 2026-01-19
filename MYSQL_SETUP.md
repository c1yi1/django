# MySQL 数据库配置说明

## 1. 安装 MySQL 客户端库

### Windows 系统：
```bash
pip install mysqlclient
```

如果安装失败，可以尝试：
```bash
pip install pymysql
```

然后在 `Django_Excem/__init__.py` 中添加：
```python
import pymysql
pymysql.install_as_MySQLdb()
```

### Linux/Mac 系统：
```bash
# 先安装 MySQL 开发库
sudo apt-get install default-libmysqlclient-dev  # Ubuntu/Debian
# 或
brew install mysql-client  # Mac

# 然后安装 Python 库
pip install mysqlclient
```

## 2. 创建 MySQL 数据库

登录 MySQL：
```bash
mysql -u root -p
```

创建数据库：
```sql
CREATE DATABASE django_exam CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## 3. 修改数据库配置

编辑 `Django_Excem/settings.py`，修改以下配置：
- `NAME`: 数据库名称（默认：django_exam）
- `USER`: MySQL 用户名（默认：root）
- `PASSWORD`: MySQL 密码（请修改为您的实际密码）
- `HOST`: 数据库主机（默认：localhost）
- `PORT`: 数据库端口（默认：3306）

## 4. 运行数据库迁移

```bash
python manage.py migrate
```

## 5. 创建超级用户（可选）

```bash
python manage.py createsuperuser
```






