from app.utils.status_code import StatusCode

class ResponseWrapper:
    @staticmethod
    def success(data=None, msg="success", code=StatusCode.SUCCESS):
        return {
            "code": int(code),
            "msg": msg,
            "data": data
        }

    @staticmethod
    def error(msg="error", code=StatusCode.FAIL, data=None):
        return {
            "code": int(code),
            "msg": msg,
            "data": data
        }