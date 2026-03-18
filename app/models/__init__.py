# model 的檔案必須要被 import 過，才會觸發繼承、才會登記進 Base.metadata
# 只 import Base 是不夠的
# Base.metadata 裡面會是空的，因為 User、Post 從來沒被 import 過
# 在 models/__init__.py 裡 import 所有 model
# 這樣只要 import Base 就會順便載入所有 model
from app.models.task import Task as Task
from app.models.user import User as User
