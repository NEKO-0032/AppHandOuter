from flask import Blueprint, jsonify, request
import flask,re

from werkzeug.security import generate_password_hash, check_password_hash
from app.extentions_reali import mysqlConnector
import mysql.connector.errors as mysql_errors

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

pattern_username = re.compile(r"^\w+$")
pattern_password = re.compile(r"^[a-zA-Z0-9!@#$%&_-]{8，70}$")

def signup_sql(username:str, password:str,permission:str="访客") ->  dict[str,int|str]:
    """
    permission必须是锁定、访客、管理员、最高管理员之一

    返回值格式（字典）：
        {
            "code": "0"（成功）/ "-1" / "-2"...（失败/报错）,
            "msg": "提示语",
            "ErrorDetails": "详细错误信息，无错误则不填"
        }
    """

    with mysqlConnector.get_cursor() as cursor:

        if username and password:
            sql = "INSERT INTO accounts (username, password_hash, permission) VALUES (%s, %s, %s)"

            """
            输入过滤
            """
            if len(password) > 70 or len(username) < 8:
                try:
                    raise AuthError("TooLongPassword")
                except AuthError as e:
                    return {"code":-1,
                            "msg":"你的密码长度不合法，应少于70个字符且大于20个字符",
                            "ErrorDetails":"",}
            if len(username) > 20:
                try:
                    raise AuthError("TooLongUsername")
                except AuthError as e:
                    return {"code":-2,
                            "msg":"你的用户名太长了，应少于20个字符",
                            "ErrorDetails":f"{e}"}

            if pattern_username.fullmatch(username) is None:
                try:
                    raise AuthError("InvalidUsername")
                except AuthError as e:
                    return {"code":-3,
                            "msg":"你的用户名包含非法字符",
                            "ErrorDetails":f"{e}"}
            if pattern_password.fullmatch(password) is None:
                try:
                    raise AuthError("InvalidPassword")
                except AuthError as e:
                    return {"code":-4,
                            "msg":"你的密码不合法",
                            "ErrorDetails":f"{e}"}





            try:
                cursor.execute(sql, (username, generate_password_hash(password), permission))
                mysqlConnector.db.commit()

            except mysql_errors.IntegrityError:
                return {"code":-5,
                        "msg":"此用户名已被使用",
                        "ErrorDetails":"IntegrityError",}
            except mysql_errors as e:
                return {"code":1,
                        "msg":f"未知错误{e}，请联系管理员寻求帮助",
                        "ErrorDetails":f"{e}",}

            return {"code":0,
                    "msg":"注册成功",
                    "ErrorDetails":"",}
        else:
            try:
                raise AuthError("EmptyInput")
            except AuthError as e:
                return {"code":2,
                        "msg":"请不要让名称或密码为空",
                        "ErrorDetails":f"{e}"}





if __name__ == "__main__":
    signup_sql("IJNKLM<.bxwarfertgjygnatz5ujsztgiktjrdsghfrxedhtgitydfrxdfghjctrftgkijkfrdctgju","wsfdexgfcdhrtjy","锁定")
    print("done")