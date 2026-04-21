from app import app
with app.test_client() as client:
    with client.session_transaction() as sess:
        sess['user_roll'] = '25101'
    res = client.post('/get_response', data={'message': 'who is my class teacher'})
    print("CLASS TEACHER:", res.get_json() if res.is_json else res.data)
    
    res = client.post('/get_response', data={'message': 'fees'})
    print("FEES:", res.get_json() if res.is_json else res.data)

    res = client.post('/get_response', data={'message': 'details of alice'})
    print("FACULTY:", res.get_json() if res.is_json else res.data)

    res = client.post('/get_response', data={'message': 'what is my next lecture'})
    print("NEXT_CLASS:", res.get_json() if res.is_json else res.data)
