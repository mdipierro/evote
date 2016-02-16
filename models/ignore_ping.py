if request.env.request_method == 'OPTIONS':
    session.forget()
    raise HTTP(200)
