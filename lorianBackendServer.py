import flask,redis,flask_jwt_extended,secrets
import io

#创建硬件资源调用实例
hardwareController = io.io()

#创建flask实例
lorianBackendServer = flask.Flask(__name__)


#设置密钥
lorianBackendServer.config['SECRET_KEY'] = secrets.token_hex(32)


#连接redis数据库
redisClient = redis.Redis(host='localhost', port=6379, db=0)

def updateLatestPackage():
    latest_file_name,latest_version = hardwareController.readLatestFile("落雨")
    redisClient.set('latest_luorian_package', latest_file_name,ex = 24 * 3600)#最新安装包文件名
    redisClient.set('latest_luorian_package_version', latest_version,ex = 24* 3600)#最新安装包版本号



@lorianBackendServer.route('/api/getLatestPackage',methods=['GET'])
def getLatestPackage():
    updateLatestPackage()
    return {'latest_package':redisClient.get('latest_luorian_package').decode(),
            'latest_version':redisClient.get('latest_luorian_package_version').decode()}


@lorianBackendServer.route('/loginServer',methods=['GET'])
def loginServer():
    return {'loginServer':'loginServer'}

if __name__ == "__main__":
    updateLatestPackage()
    lorianBackendServer.run(debug=True)
























