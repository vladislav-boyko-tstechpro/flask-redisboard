import json


def test_home_redirect(client):
    rv = client.get("/")
    assert rv.status_code == 302


def test_blueprint_index_redirect(client):
    rv = client.get("/redisboard/")
    assert rv.status_code == 302


def test_dashboard(client):
    rv = client.get("/redisboard/dashboard/")
    assert rv.status_code == 200
    assert b"Total Memory" in rv.data


def test_dashboard_api(client):
    rv = client.get("/redisboard/dashboard_api/")
    assert rv.status_code == 200
    res = rv.get_json()
    assert res["code"] == 0
    assert "memory" in res["data"]


def test_info(client):
    rv = client.get("/redisboard/info/")
    assert rv.status_code == 200
    assert b"SlowlogTable" in rv.data


def test_config(client):
    rv = client.get("/redisboard/config/")
    assert rv.status_code == 200
    assert b"LATENCY MONITOR" in rv.data

    rv = client.post("/redisboard/config/", data=dict(name="maxclients", value="9999"))
    assert rv.get_json()["code"] == 0


def test_db(client):
    rv = client.get("/redisboard/db/")
    assert rv.status_code == 200
    assert b"Separate multiple" in rv.data

    # with cursor should response json
    rv = client.get("/redisboard/db/?cursor=1")
    res = rv.get_json()
    assert res["code"] == 0
    assert "/redisboard/db/" in res["data"] or res["data"] is ""


def test_add_and_get_key(client):
    str_test = dict(type="string", keyname="a", value="astring")
    list_test = dict(type="list", keyname="b", value="1,3335,5")
    hash_test = dict(type="hash", keyname="c", index="hashkey", value="hashvalue")
    set_test = dict(type="set", keyname="d", value="1919,3,1919")
    zset_test = dict(type="zset", keyname="e", index="1233", value="zsetvalue")

    rv = client.post("/redisboard/db/2/addkey", data=str_test)
    assert rv.status_code == 302
    rv = client.get("/redisboard/db/2/a")
    assert rv.status_code == 200
    assert b"astring" in rv.data

    rv = client.post("/redisboard/db/2/addkey", data=list_test)
    assert rv.status_code == 302
    rv = client.get("/redisboard/db/2/b")
    assert rv.status_code == 200
    assert b"3335" in rv.data

    rv = client.post("/redisboard/db/2/addkey", data=hash_test)
    assert rv.status_code == 302
    rv = client.get("/redisboard/db/2/c")
    assert rv.status_code == 200
    assert b"hashvalue" in rv.data

    rv = client.post("/redisboard/db/2/addkey", data=set_test)
    assert rv.status_code == 302
    rv = client.get("/redisboard/db/2/d")
    assert rv.status_code == 200
    assert b"1919" in rv.data

    rv = client.post("/redisboard/db/2/addkey", data=zset_test)
    assert rv.status_code == 302
    rv = client.get("/redisboard/db/2/e")
    assert rv.status_code == 200
    assert b"zsetvalue" in rv.data
    assert b"1233" in rv.data


def test_delete_key(client):
    rv = client.post(
        "/redisboard/db/2/addkey",
        data=dict(type="string", keyname="testdelkey", value="0"),
    )
    assert rv.status_code == 302
    # miss not exist key report error
    # rv = client.delete("/redisboard/db/2/key/notexistkey/del")
    # assert rv.status_code == 404
    rv = client.delete("/redisboard/db/2/key/testdelkey/del")
    assert rv.get_json()["code"] == 0


def test_rename_key(client):
    rv = client.post(
        "/redisboard/db/2/addkey",
        data=dict(type="string", keyname="testrenamekey", value="0"),
    )
    assert rv.status_code == 302
    rv = client.post(
        "/redisboard/db/2/testrenamekey/rename", data=dict(keyname="renamed")
    )
    assert rv.get_json()["code"] == 0
    rv = client.get("/redisboard/db/2/testrenamekey")
    res = rv.get_json()
    assert res["code"] == 999
    assert "404" in res["error"]
    rv = client.get("/redisboard/db/2/renamed")
    assert rv.status_code == 200


def test_set_ttl_key(client):
    rv = client.post(
        "/redisboard/db/2/addkey",
        data=dict(type="string", keyname="testttl", value="0"),
    )
    assert rv.status_code == 302
    rv = client.post("/redisboard/db/2/testttl/ttl", data=dict(ttl=2000))
    assert rv.get_json()["code"] == 0
    rv = client.post("/redisboard/db/2/testttl/ttl", data=dict(ttl=-100))
    assert rv.get_json()["code"] == 0
    rv = client.get("/redisboard/db/2/testttl")
    assert rv.status_code == 200
    assert b"forever" in rv.data


def test_batch_set_ttl(client):
    rv = client.post(
        "/redisboard/db/2/batchttl",
        data=json.dumps(dict(keys=["a", "b", "c"], ttl=36000)),
        content_type="application/json",
    )
    assert rv.status_code == 200
    assert rv.get_json()["code"] == 0
    rv = client.post(
        "/redisboard/db/2/batchttl",
        data=json.dumps(dict(keys=["a", "b", "c"], ttl=-1)),
        content_type="application/json",
    )
    assert rv.status_code == 200
    assert rv.get_json()["code"] == 0


def test_batch_delete(client):
    rv = client.post(
        "/redisboard/db/2/addkey",
        data=dict(type="string", keyname="testdel1", value="0"),
    )
    assert rv.status_code == 302
    rv = client.post(
        "/redisboard/db/2/addkey",
        data=dict(type="string", keyname="testdel2", value="0"),
    )
    assert rv.status_code == 302
    rv = client.post(
        "/redisboard/db/2/batchdel",
        data=json.dumps(dict(keys=["testdel1", "testdel2"])),
        content_type="application/json",
    )
    assert rv.status_code == 200
    assert rv.get_json()["code"] == 0


def test_list(client):
    rv = client.post(
        "/redisboard/db/2/addkey", data=dict(type="list", keyname="test_list"),
    )
    assert rv.status_code == 200

    # test add multi list key
    rv = client.post(
        "/redisboard/db/2/test_list/list_add", data=dict(value="lista0", position=-1),
    )
    assert rv.status_code == 200
    assert rv.get_json()["code"] == 0
    rv = client.post(
        "/redisboard/db/2/test_list/list_add", data=dict(value="listb1", position=0)
    )
    assert rv.status_code == 200
    assert rv.get_json()["code"] == 0
    rv = client.get("/redisboard/db/2/test_list")
    assert b"listb1" in rv.data

    # test edit and remove list key
    rv = client.post(
        "/redisboard/db/2/test_list/list_edit", data=dict(name=0, value="listc2")
    )
    assert rv.get_json()["code"] == 0
    rv = client.post("/redisboard/db/2/test_list/list_rem", data=dict(value="lista0"))
    assert rv.get_json()["code"] == 0
    rv = client.get("/redisboard/db/2/test_list")
    assert b"listc2" in rv.data
    assert b"lista0" not in rv.data
    assert b"listb1" not in rv.data

    rv = client.delete("/redisboard/db/2/key/test_list/del")
    assert rv.get_json()["code"] == 0


def test_hash(client):
    rv = client.post(
        "/redisboard/db/2/addkey", data=dict(type="hash", keyname="test_hash"),
    )
    assert rv.status_code == 200

    # test add hash key
    rv = client.post(
        "/redisboard/db/2/test_hash/hash_add",
        data=dict(index="hashkey", value="hashvalue"),
    )
    assert rv.status_code == 200
    assert rv.get_json()["code"] == 0
    rv = client.post(
        "/redisboard/db/2/test_hash/hash_add",
        data=dict(index="hashkey", value="hashvalue"),
    )
    assert rv.status_code == 200
    assert rv.get_json()["code"] == 1  # add exist key should error code 1
    rv = client.get("/redisboard/db/2/test_hash")
    assert b"hashkey" in rv.data
    assert b"hashvalue" in rv.data

    # test edit hash key
    rv = client.post(
        "/redisboard/db/2/test_hash/hash_edit",
        data=dict(name="hashkey", value="hash_edited_value"),
    )
    assert rv.get_json()["code"] == 0
    rv = client.get("/redisboard/db/2/test_hash")
    assert b"hashvalue" not in rv.data
    assert b"hash_edited_value" in rv.data

    # test remove hash key
    rv = client.post("/redisboard/db/2/test_hash/hash_rem", data=dict(index="hashkey"))
    assert rv.get_json()["code"] == 0
    rv = client.get("/redisboard/db/2/test_list")
    assert b"hashkey" not in rv.data

    rv = client.delete("/redisboard/db/2/key/test_hash/del")
    assert rv.get_json()["code"] == 0


def test_set(client):
    rv = client.post(
        "/redisboard/db/2/addkey", data=dict(type="set", keyname="test_set"),
    )
    assert rv.status_code == 200

    # test add set key
    rv = client.post(
        "/redisboard/db/2/test_set/set_add", data=dict(value="224,123,224,345"),
    )
    assert rv.status_code == 200
    assert rv.get_json()["code"] == 0
    rv = client.get("/redisboard/db/2/test_set")
    assert b"224" in rv.data
    assert b"345" in rv.data

    # test remove set key
    rv = client.post("/redisboard/db/2/test_set/set_rem", data=dict(value="224,123"))
    assert rv.get_json()["code"] == 0
    rv = client.get("/redisboard/db/2/test_set")
    assert b"224" not in rv.data
    assert b"123" not in rv.data

    rv = client.delete("/redisboard/db/2/key/test_set/del")
    assert rv.get_json()["code"] == 0


def test_zset(client):
    rv = client.post(
        "/redisboard/db/2/addkey", data=dict(type="zset", keyname="test_zset"),
    )
    assert rv.status_code == 200

    # test add zset key
    rv = client.post(
        "/redisboard/db/2/test_zset/zset_add", data=dict(member="abc", score=3.1415926),
    )
    assert rv.status_code == 200
    assert rv.get_json()["code"] == 0
    rv = client.post(
        "/redisboard/db/2/test_zset/zset_add", data=dict(member="def", score=3.1415927),
    )
    assert rv.status_code == 200
    assert rv.get_json()["code"] == 0
    rv = client.post(
        "/redisboard/db/2/test_zset/zset_add", data=dict(member="hjk", score=3.1415928),
    )
    assert rv.status_code == 200
    assert rv.get_json()["code"] == 0
    rv = client.post(
        "/redisboard/db/2/test_zset/zset_add", data=dict(member="lmn", score=2.1234),
    )
    assert rv.status_code == 200
    assert rv.get_json()["code"] == 0
    rv = client.get("/redisboard/db/2/test_zset")
    assert b"3.1415926" in rv.data
    assert b"3.1415927" in rv.data

    # test edit and remove zset key
    rv = client.post(
        "/redisboard/db/2/test_zset/zset_edit", data=dict(name="abc", value=4.2345)
    )
    assert rv.get_json()["code"] == 0
    rv = client.post("/redisboard/db/2/test_zset/zset_rem", data=dict(min=3.0, max=4.0))
    assert rv.get_json()["code"] == 0
    rv = client.post("/redisboard/db/2/test_zset/zset_rem", data=dict(member="lmn"))
    assert rv.get_json()["code"] == 0
    rv = client.get("/redisboard/db/2/test_zset")
    assert b"3.1415926" not in rv.data
    assert b"3.1415927" not in rv.data
    assert b"3.1415928" not in rv.data
    assert b"2.1234" not in rv.data
    assert b"4.2345" in rv.data

    rv = client.delete("/redisboard/db/2/key/test_zset/del")
    assert rv.get_json()["code"] == 0


def test_command(client):
    rv = client.get("/redisboard/command/")
    assert b"Command Mode" in rv.data

    rv = client.post("/redisboard/command/", data=dict(command="ping"))
    assert rv.get_json()["code"] == 0
