import httpx

def captcha(gt: str, challenge: str, endpoint: str = "http://127.0.0.1:9645/pass_nine"):
    """
    通用的验证码处理函数
    参数:
        gt: 验证码的 gt 参数
        challenge: 验证码的 challenge 参数
        endpoint: API 的端点 URL，默认为 "http://127.0.0.1:9645/pass_nine"
    返回:
        成功时返回 validate 字符串，失败时返回 None
    """
    try:
        res = httpx.get(
            endpoint,
            params={'gt': gt, 'challenge': challenge, 'use_v3_model': True},
            timeout=10
        )
        # 解析响应数据
        datas = res.json().get('data', {})
        if datas.get('result') == 'success':
            return datas.get('validate')
    except (httpx.RequestError, KeyError) as e:
        # 捕获网络错误或数据解析错误
        print(f"Error during captcha processing: {e}")
    return None  # 失败时返回 None

def game_captcha(gt: str, challenge: str):
    """
    游戏验证码处理
    """
    return captcha(gt, challenge)

def bbs_captcha(gt: str, challenge: str):
    """
    BBS 验证码处理
    """
    return captcha(gt, challenge)

# 示例调用
if __name__ == "__main__":
    gt = "example_gt"
    challenge = "example_challenge"
    
    # 调用 game_captcha
    result = game_captcha(gt, challenge)
    print(f"Game captcha result: {result}")

    # 调用 bbs_captcha
    result = bbs_captcha(gt, challenge)
    print(f"BBS captcha result: {result}")
