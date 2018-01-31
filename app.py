import os
import json
import requests
import tornado.ioloop
import tornado.web
import tornado.websocket
import websocket
# from socketIO_client import SocketIO

from tornado.options import define, options, parse_command_line

define("port", default=8888, help="run on the given port", type=int)
define("debug", type=bool, default=True)

# we gonna store clients in dictionary..
clients = dict()


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/home/", HomeHandler),
            (r"/telegram/", TelegramHandler),
            (r"/send_message/", SendMessageHandler),
            (r"/", IndexHandler),
            (r"/ws/", WebSocketHandler),
        ]
        settings = dict(
            debug=True,
            autoreload=True,
            static_path=os.path.join(os.path.dirname(__file__), "static"),
        )
        tornado.web.Application.__init__(self, handlers,
                                         dict(path=settings['static_path']),
                                         **settings)


class SendMessageHandler(tornado.web.RequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message = None

    def post(self, *args, **kwargs):
        self.message = self.request.body_arguments.get('message')
        recipients = [clients[client]['object'] for client in clients]
        self.message = ''.join(map(str, self.message))
        if recipients and self.message:
            WebSocketHandler.send_message(recipients=recipients, message=self.message)
        else:
            print('Nothing to send')


class HomeHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        self.render('templates/home.html')


class TelegramHandler(tornado.web.RequestHandler):
    """
    https://api.telegram.org/bot[BOT_API_KEY]/sendMessage?chat_id=[MY_CHANNEL_NAME]&text=[MY_MESSAGE_TEXT]
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.BOT_API_KEY = '517737139:AAHaPhhzg5fxPz3tL2cAUmU19Y_ez0lQ4VI'
        self.MY_CHANNEL_NAME = '@yltnews'
        self.url = 'https://api.telegram.org/bot{}/sendMessage?'.format(self.BOT_API_KEY)
        self.message = []
        self.about_bot = ''

    @tornado.web.asynchronous
    def get(self):
        self.render('templates/telegram.html')

    def post(self, *args, **kwargs):
        self.message = self.request.body_arguments.get('tg-message')
        r = requests.get(url=self.url,
                         params={'chat_id': self.MY_CHANNEL_NAME,
                                 'text': self.message[0].decode()})
        if r.status_code != 200:
            print('error when sending messsage to Telegram Channel')
            return False
        self.about_bot = requests.get(url='https://api.telegram.org/bot{}/getMe'.format(self.BOT_API_KEY),)

        self.render('templates/telegram.html',
                     )

class IndexHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        self.render('templates/index.html')


class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def open(self, *args):
        self.id = id(self.request)
        # self.stream.set_nodelay(True)
        clients[self.id] = {"id": self.id, "object": self}
        self.write_message('Client added', str(self.id))
        print('Client added', str(self.id))

    def on_message(self, message):
        """
        when we receive some message we want some message handler..
        for this example i will just print message to console
        """
        # print("Client %s received a message : %s" % (self.id, message))
        # print(clients)
        # self.write_message(json.dumps(list(clients.keys())))
        pass

    def on_close(self):
        if self.id in clients:
            del clients[self.id]

    def check_origin(self, origin):
        return True

    @classmethod
    def send_message(cls, recipients=list(), message=None):
        for recipient in recipients:
            recipient.write_message(message)
            print('message to', recipient, 'sent')


class Client(object):
    def __init__(self, url, timeout):
        self.url = url
        self.timeout = timeout
        self.ioloop = tornado.ioloop.IOLoop.instance()
        self.ws = None
        self.connect()
        tornado.ioloop.PeriodicCallback(self.keep_alive, 20000, io_loop=self.ioloop).start()
        self.ioloop.start()

    @tornado.gen.coroutine
    def connect(self):
        print("trying to connect")
        try:

            self.ws = yield websocket.create_connection(
                'wss://streamer.cryptocompare.com/socket.io/?transport=websocket',
                timeout=5
            )
            self.ws.send('SubAdd', {'subs': ['0~Poloniex~BTC~USD']})
            # self.ws.wait()
        except Exception as e:
            print("connection error", e)
        else:
            print("connected")
            # subscription = ['5~CCCAGG~BTC~USD', '5~CCCAGG~ETH~USD']
            # self.ws.write_message('SubAdd', {'subs': subscription})
            self.run()

    @tornado.gen.coroutine
    def run(self):
        while True:
            msg = yield self.ws.read_message()
            if msg is None:
                print("connection closed")
                self.ws = None
                break
            # print(msg)
            WebSocketHandler.send_message(
                recipients=[clients[client]['object'] for client in clients],
                message=msg
            )

    def keep_alive(self):
        if self.ws is None:
            self.connect()
        else:
            self.ws.write_message("keep alive")


if __name__ == '__main__':
    parse_command_line()
    app = Application()
    app.listen(options.port)
    print('Server started on {} port'.format(options.port))
    client = Client("https://streamer.cryptocompare.com/", 5)
    tornado.ioloop.IOLoop.instance().start()
