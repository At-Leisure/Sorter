

# local module
import utils


@utils.asEnumClass()
class VideoState:
    """ 视频播放状态 """
    FINISHED = 0  # 播放完成
    RUNNING = 1  # 正在播放
