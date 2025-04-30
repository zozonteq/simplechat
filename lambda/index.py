# lambda/index.py
import json
import urllib.request
import os
from urllib.error import HTTPError, URLError
import boto3
import re  # 正規表現モジュールをインポート
from botocore.exceptions import ClientError

# python_client.py
# このコードは、ngrokで公開されたAPIにアクセスするPythonクライアントの例です

import json
import time

# APIエンドポイントの設定
API_ENDPOINT = os.environ.get("API_ENDPOINT", "https://4bf1-34-125-222-117.ngrok-free.app/generate")

class LLMClient:
    """LLM API クライアントクラス"""
    
    def __init__(self, api_url):
        """
        初期化
        
        Args:
            api_url (str): API のベース URL
        """
        self.api_url = api_url
    
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
        
        data = json.dumps(payload).encode("utf-8")
        
        try:
            req = urllib.request.Request(
                self.api_url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            
            with urllib.request.urlopen(req) as res:
                response_json = json.loads(res.read().decode("utf-8"))
                return response_json
                
        except HTTPError as e:
            error_message = f"HTTP Error: {e.code} - {e.reason}"
            if e.readable():
                error_message += f"\nResponse: {e.read().decode('utf-8')}"
            raise Exception(error_message)
        except URLError as e:
            raise Exception(f"URL Error: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"JSON Decode Error: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error: {str(e)}")

# グローバルクライアントインスタンス
llm_client = LLMClient(API_ENDPOINT)

def lambda_handler(event, context):
    try:
        # リクエストボディの解析
        body = json.loads(event.get("body", "{}"))
        message = body.get("message", "")
        
        if not message:
            raise ValueError("Message is required")
        
        # LLMクライアントを使用してテキスト生成
        response = llm_client.generate(message)
        
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
                "response": response.get("generated_text", ""),
                "conversationHistory": []
            })
        }
        
    except ValueError as e:
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": False,
                "error": str(e)
            })
        }
    except Exception as e:
        print(f"Error: {str(e)}")
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
                "error": str(e)
            })
        }

# Lambda コンテキストからリージョンを抽出する関数
def extract_region_from_arn(arn):
    # ARN 形式: arn:aws:lambda:region:account-id:function:function-name
    match = re.search('arn:aws:lambda:([^:]+):', arn)
    if match:
        return match.group(1)
    return "us-east-1"  # デフォルト値

# グローバル変数としてクライアントを初期化（初期値）
bedrock_client = None

# モデルID
MODEL_ID = os.environ.get("MODEL_ID", "us.amazon.nova-lite-v1:0")
