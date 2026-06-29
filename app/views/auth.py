from flask import Blueprint, jsonify, request
import flask

from werkzeug.security import generate_password_hash, check_password_hash
from app.extentions_reali import mysqlConnector

# 创建蓝图
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
#创建Mysql连接实例
class AuthError(Exception):
    pass




@auth_bp.route('/login', methods=['POST'])
def login():
    """
    登录接口（待完善）
    后续需要添加：
    - 用户名密码验证
    - JWT token 生成
    - 速率限制
    - 验证码
    """
    form = request.form
    
    if not form:
        return jsonify({'error': '请求数据不能为空'}), 400
    
    username = form.get('username')
    password = form.get('password')
    
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400
    
    # TODO: 实现真正的登录逻辑
    # 1. 从数据库查询用户
    # 2. 验证密码（使用 check_password_hash）
    # 3. 生成 JWT token
    
    return jsonify({'message': '登录功能待实现', 'username': username}), 200


@auth_bp.route("/login", methods=["GET"])
def login_page_get():
    return flask.render_template("login.html")


def signup_sql(username, password,permission="访客"):
    """"
    permission必须是锁定、访客、管理员、最高管理员之一
    """

    with mysqlConnector.get_cursor() as cursor:
        if username and password:
            sql = "INSERT INTO accounts (username, password_hash, permission) VALUES (%s, %s, %s)"
            if len(password) > 70:
                raise AuthError("The password is too long.")
            cursor.execute(sql, (username, generate_password_hash(password), permission))
            mysqlConnector.db.commit()




if __name__ == "__main__":
    signup_sql("test","wsfdexgfcdhrtjy","锁定")
    print("done")