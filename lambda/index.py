# lambda/index.py
import json
import os
import boto3
import re  # 正規表現モジュールをインポート
from botocore.exceptions import ClientError

# python_client.py
# このコードは、ngrokで公開されたAPIにアクセスするPythonクライアントの例です

import requests
import json
import time

class LLMClient:
    """LLM API クライアントクラス"""
    
    def __init__(self, api_url):
        """
        初期化
        
        Args:
            api_url (str): API のベース URL（ngrok URL）
        """
        self.api_url = api_url.rstrip('/')
        self.session = requests.Session()
    
    def health_check(self):
        """
        ヘルスチェック
        
        Returns:
            dict: ヘルスチェック結果
        """
        response = self.session.get(f"{self.api_url}/health")
        return response.json()
    
    def generate(self, prompt, max_new_tokens=512, temperature=0.7, top_p=0.9, do_sample=True):
        """
        テキスト生成
        
        Args:
            prompt (str): プロンプト文字列
            max_new_tokens (int, optional): 生成する最大トークン数
            temperature (float, optional): 温度パラメータ
            top_p (float, optional): top-p サンプリングのパラメータ
            do_sample (bool, optional): サンプリングを行うかどうか
        
        Returns:
            dict: 生成結果
        """
        payload = {
            "prompt": prompt,
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "do_sample": do_sample
        }
        
        start_time = time.time()
        response = self.session.post(
            f"{self.api_url}/generate",
            json=payload
        )
        total_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            result["total_request_time"] = total_time
            return result
        else:
            raise Exception(f"API error: {response.status_code} - {response.text}")


# Lambda コンテキストからリージョンを抽出する関数
def extract_region_from_arn(arn):
    # ARN 形式: arn:aws:lambda:region:account-id:function:function-name
    match = re.search('arn:aws:lambda:([^:]+):', arn)
    if match:
        return match.group(1)
    return "us-east-1"  # デフォルト値

# グローバル変数としてクライアントを初期化（初期値）
bedrock_client = None

API_ENDPOINT = "https://87ae-34-125-46-174.ngrok-free.app/"

# モデルID
MODEL_ID = os.environ.get("MODEL_ID", "us.amazon.nova-lite-v1:0")
LLM_CLIENT = LLMClient(API_ENDPOINT)

def lambda_handler(event, context):
    try:
        assistant_response = LLM_CLIENT.generate(event["body"]["message"])

        # コンテキストから実行リージョンを取得し、クライアントを初期化
        
        # 成功レスポンスの返却
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": True,
                "response": assistant_response,
                "conversationHistory": []
            })
        }
        
    except Exception as error:
        print("Error:", str(error))
        
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": False,
                "error": str(error)
            })
        }
