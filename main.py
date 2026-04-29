from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import requests
import os

# ========== НАСТРОЙКИ (ЗАМЕНИТЕ НА СВОИ) ==========
BOT_TOKEN = "7954236837:AAEEG4wsxqT8IxRHxZkvRtviavfmjsLl7fE"  # Получить у @id199142634 (@BotFather)
ADMIN_CHAT_ID = "423565197"  # Получить у @userinfobot
BASE_URL = "https://ВАШ-ДОМЕН.com"  # Ваш HTTPS-адрес после деплоя

# ========== БАЗА ДАННЫХ ==========
engine = create_engine("sqlite:///./orders.db")
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    client_name = Column(String, nullable=False)
    client_phone = Column(String, nullable=False)
    business_type = Column(String, nullable=False)  # Тип бизнеса клиента
    status = Column(String, default="🟡 Новый")
    created_at = Column(DateTime, default=datetime.now)


Base.metadata.create_all(bind=engine)

# ========== FASTAPI ==========
app = FastAPI()


class OrderCreate(BaseModel):
    client_name: str
    client_phone: str
    business_type: str


# ========== HTML MiniApp (продающий сам себя) ==========
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Бот для приема заказов | Под ключ</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 500px;
            margin: 0 auto;
            background: white;
            border-radius: 32px;
            padding: 24px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        h1 {
            font-size: 28px;
            color: #1a1a2e;
            margin-bottom: 8px;
        }
        .badge {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 8px 16px;
            border-radius: 40px;
            font-size: 14px;
            font-weight: 600;
            display: inline-block;
            margin-bottom: 20px;
        }
        .price {
            font-size: 36px;
            font-weight: bold;
            color: #667eea;
            margin: 20px 0;
        }
        .price small {
            font-size: 16px;
            font-weight: normal;
            color: #666;
        }
        .feature {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 0;
            border-bottom: 1px solid #eee;
        }
        .feature:before {
            content: "";
            font-size: 20px;
        }
        input, select, button {
            width: 100%;
            padding: 14px;
            margin: 10px 0;
            border-radius: 16px;
            border: 2px solid #e0e0e0;
            font-size: 16px;
            transition: all 0.3s;
        }
        input:focus, select:focus {
            outline: none;
            border-color: #667eea;
        }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-weight: bold;
            border: none;
            cursor: pointer;
            font-size: 18px;
            margin-top: 20px;
        }
        button:hover {
            transform: scale(1.02);
            opacity: 0.95;
        }
        #status {
            margin-top: 20px;
            padding: 12px;
            border-radius: 12px;
            display: none;
            text-align: center;
        }
        .divider {
            text-align: center;


margin: 24px 0;
            color: #999;
        }
    </style>
</head>
<body>
    <div class="container">
        <span class="badge">⚡ Под ключ за 24 часа</span>
        <h1> Telegram бот для приема заказов</h1>
        <div class="price">
            от $149 <small>/ полностью готовый</small>
        </div>

        <div class="feature">Автоматический прием заявок 24/7</div>
        <div class="feature">Уведомления владельцу в Telegram</div>
        <div class="feature">База данных всех клиентов</div>
        <div class="feature">Настройка под ваш бизнес за 1 день</div>
        <div class="feature">Бесплатная техническая поддержка 1 месяц</div>

        <div class="divider">━━━━━━━━━━━━━━━━━━━━</div>

        <h3 style="margin-bottom: 16px;"> Оставьте заявку — мы свяжемся с вами</h3>

        <form id="orderForm">
            <input type="text" id="client_name" placeholder="Ваше имя" required>
            <input type="tel" id="client_phone" placeholder="Ваш телефон" required>
            <select id="business_type" required>
                <option value="">Выберите ваш бизнес</option>
                <option value=" Интернет-магазин"> Интернет-магазин</option>
                <option value=" Клининг / мойка окон"> Клининг / мойка окон</option>
                <option value="️ Салон красоты">️ Салон красоты</option>
                <option value=" Доставка еды"> Доставка еды</option>
                <option value=" Репетитор / онлайн-школа"> Репетитор / онлайн-школа</option>
                <option value=" Ремонт / услуги мастера"> Ремонт / услуги мастера</option>
                <option value=" Другое"> Другое</option>
            </select>
            <button type="submit"> Заказать бота</button>
        </form>
        <div id="status"></div>
    </div>

    <script>
        const form = document.getElementById('orderForm');
        const statusDiv = document.getElementById('status');

        form.onsubmit = async (e) => {
            e.preventDefault();
            const data = {
                client_name: document.getElementById('client_name').value,
                client_phone: document.getElementById('client_phone').value,
                business_type: document.getElementById('business_type').value
            };

            if (!data.business_type) {
                statusDiv.style.display = 'block';
                statusDiv.innerHTML = 'Пожалуйста, выберите тип бизнеса';
                statusDiv.style.background = '#f8d7da';
                return;
            }

            statusDiv.style.display = 'block';
            statusDiv.innerHTML = 'Отправка заявки...';
            statusDiv.style.background = '#e3f2fd';

            try {
                const res = await fetch('/api/order', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                const result = await res.json();
                if (res.ok) {
                    statusDiv.innerHTML = '✅ Спасибо! Мы свяжемся с вами в течение 30 минут.';
                    statusDiv.style.background = '#d4edda';
                    form.reset();

                    // Закрываем мини-приложение через 2 секунды (опционально)
                    setTimeout(() => {
                        if (window.Telegram?.WebApp) {
                            window.Telegram.WebApp.close();
                        }
                    }, 2000);
                } else {
                    statusDiv.innerHTML = 'Ошибка: ' + (result.detail || 'попробуйте позже');
                    statusDiv.style.background = '#f8d7da';
                }
            } catch (err) {
                statusDiv.innerHTML = 'Ошибка соединения. Проверьте интернет.';
                statusDiv.style.background = '#f8d7da';
            }
        };
    </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def get_miniapp():


    return HTML_TEMPLATE

"/api/order"


async def create_order(order: OrderCreate):
    db = SessionLocal()
    try:
        new_order = Order(
            client_name=order.client_name,
            client_phone=order.client_phone,
            business_type=order.business_type
        )
        db.add(new_order)
        db.commit()
        db.refresh(new_order)

        # Отправляем уведомление АДМИНИСТРАТОРУ (вам)
        message = f"""**НОВАЯ ЗАЯВКА НА БОТА!**

name: {order.client_name}
phone: {order.client_phone}
business: {order.business_type}
application_number: {new_order.id}

{datetime.now().strftime('%d.%m.%Y %H:%M')}"""

        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage&quot;,
        json = {
            "chat_id": ADMIN_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        )

        return {"status": "ok", "order_id": new_order.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# ========== ЗАПУСК ==========
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)