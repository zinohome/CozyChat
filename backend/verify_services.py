#!/usr/bin/env python3
"""
验证外部服务连接

用于验证PostgreSQL和Redis服务是否可用
"""

import sys

def test_postgresql():
    """测试PostgreSQL连接"""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host='192.168.66.10',
            port=5432,
            database='cozychat_test',
            user='cozychat_test',
            password='passw0rd',
            connect_timeout=5
        )
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        print("✅ PostgreSQL连接成功")
        return True
    except ImportError:
        print("⚠️ psycopg2未安装，跳过PostgreSQL测试")
        return False
    except Exception as e:
        print(f"❌ PostgreSQL连接失败: {e}")
        return False


def test_redis():
    """测试Redis连接"""
    try:
        import redis
        r = redis.Redis(
            host='192.168.66.10',
            port=6379,
            password='redis_passw0rd',
            socket_connect_timeout=5,
            decode_responses=True
        )
        r.ping()
        # 测试基本操作
        r.set("test_key", "test_value", ex=10)
        value = r.get("test_key")
        r.delete("test_key")
        if value == "test_value":
            print("✅ Redis连接成功，基本操作正常")
            return True
        else:
            print("⚠️ Redis连接成功，但操作异常")
            return False
    except ImportError:
        print("⚠️ redis未安装，跳过Redis测试")
        return False
    except Exception as e:
        print(f"❌ Redis连接失败: {e}")
        return False


def test_three_engines():
    """测试三大引擎连接"""
    import httpx
    
    engines = [
        ("Cognee", "http://192.168.66.11:8000"),
        ("Memobase", "http://192.168.66.11:8019"),
        ("Mem0", "http://192.168.66.11:8888"),
    ]
    
    results = {}
    for name, url in engines:
        try:
            response = httpx.get(f"{url}/health", timeout=3)
            if response.status_code == 200:
                print(f"✅ {name}连接成功 ({url})")
                results[name] = True
            else:
                print(f"⚠️ {name}响应异常: {response.status_code} ({url})")
                results[name] = False
        except Exception as e:
            print(f"❌ {name}连接失败: {e} ({url})")
            results[name] = False
    
    return all(results.values())


if __name__ == "__main__":
    print("=" * 60)
    print("验证外部服务连接")
    print("=" * 60)
    print()
    
    results = {}
    results["PostgreSQL"] = test_postgresql()
    print()
    results["Redis"] = test_redis()
    print()
    results["三大引擎"] = test_three_engines()
    print()
    
    print("=" * 60)
    print("验证结果汇总")
    print("=" * 60)
    for service, success in results.items():
        status = "✅ 可用" if success else "❌ 不可用"
        print(f"{service}: {status}")
    
    if all(results.values()):
        print("\n🎉 所有服务可用，可以运行完整测试！")
        sys.exit(0)
    else:
        print("\n⚠️ 部分服务不可用，请检查配置")
        sys.exit(1)

