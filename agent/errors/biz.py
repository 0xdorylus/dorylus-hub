from agent.errors.base import BaseError

class AccountRegisterError(BaseError):
    pass

class AccountLoginError(BaseError):
    pass
class UserUploadError(BaseError):
    pass


class AgentNotFoundError(BaseError):
    pass

class UserNotInChannel(BaseError):
    pass