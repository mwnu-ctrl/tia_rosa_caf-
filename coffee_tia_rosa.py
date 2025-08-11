"""
coffee_tia_rosa.py

Sistema simples de gerenciamento para a cafeteria "Coffee Shops Tia Rosa".
Modo de uso:
  - Executar interativamente: python coffee_tia_rosa.py
  - Ou usar modo demo para ver um fluxo de exemplo: python coffee_tia_rosa.py --demo
"""

import json
import os
import datetime
import uuid
from typing import List, Dict

# Se executado como script normal, __file__ existe e define DATA_DIR relativo ao arquivo.
# Se o módulo for importado dentro de outro processo (ex: exec), __file__ pode não existir.
if "__file__" in globals():
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
else:
    # padrão para o ambiente desta execução: /mnt/data/coffee_tia_rosa_project
    SCRIPT_DIR = os.path.join(os.getcwd(), "coffee_tia_rosa_project")

DATA_DIR = os.path.join(SCRIPT_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

def _save_json(filename, data):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def _load_json(filename, default):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

class Product:
    def __init__(self, name: str, price: float, stock: int, description: str = "", category: str = ""):
        self.id = str(uuid.uuid4())[:8]
        self.name = name
        self.price = round(float(price), 2)
        self.stock = int(stock)
        self.description = description
        self.category = category

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "price": self.price,
            "stock": self.stock,
            "description": self.description,
            "category": self.category
        }

    @staticmethod
    def from_dict(d):
        p = Product(d["name"], d["price"], d["stock"], d.get("description",""), d.get("category",""))
        p.id = d["id"]
        return p

class Customer:
    def __init__(self, name: str, phone: str = "", email: str = ""):
        self.id = str(uuid.uuid4())[:8]
        self.name = name
        self.phone = phone
        self.email = email
        self.points = 0  # programa de fidelidade simples

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "phone": self.phone,
            "email": self.email,
            "points": self.points
        }

    @staticmethod
    def from_dict(d):
        c = Customer(d["name"], d.get("phone",""), d.get("email",""))
        c.id = d["id"]
        c.points = d.get("points", 0)
        return c

class Order:
    def __init__(self, customer_id: str = None):
        self.id = str(uuid.uuid4())[:10]
        self.customer_id = customer_id
        self.items = []  # list of (product_id, name, unit_price, quantity)
        self.created_at = datetime.datetime.now().isoformat()

    def add_item(self, product_id, name, unit_price, qty):
        self.items.append({
            "product_id": product_id,
            "name": name,
            "unit_price": round(unit_price,2),
            "quantity": int(qty),
            "subtotal": round(unit_price * qty, 2)
        })

    def total(self):
        return round(sum(item["subtotal"] for item in self.items), 2)

    def to_dict(self):
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "items": self.items,
            "created_at": self.created_at,
            "total": self.total()
        }

class CoffeeSystem:
    def __init__(self):
        self.products: Dict[str, Product] = {}
        self.customers: Dict[str, Customer] = {}
        self.orders: Dict[str, Order] = {}
        self.load_all()

    # Persistence
    def load_all(self):
        products = _load_json("products.json", [])
        customers = _load_json("customers.json", [])
        orders = _load_json("orders.json", [])
        for p in products:
            prod = Product.from_dict(p)
            self.products[prod.id] = prod
        for c in customers:
            cus = Customer.from_dict(c)
            self.customers[cus.id] = cus
        for o in orders:
            self.orders[o["id"]] = o

    def save_all(self):
        _save_json("products.json", [p.to_dict() for p in self.products.values()])
        _save_json("customers.json", [c.to_dict() for c in self.customers.values()])
        _save_json("orders.json", [o for o in self.orders.values()])

    # Product management
    def add_product(self, name, price, stock, description="", category=""):
        p = Product(name, price, stock, description, category)
        self.products[p.id] = p
        self.save_all()
        return p

    def edit_product(self, product_id, **kwargs):
        if product_id not in self.products:
            raise KeyError("Produto não encontrado")
        p = self.products[product_id]
        for k,v in kwargs.items():
            if hasattr(p, k):
                setattr(p, k, v)
        self.save_all()
        return p

    def list_products(self):
        return [p.to_dict() for p in self.products.values()]

    # Customer management
    def add_customer(self, name, phone="", email=""):
        c = Customer(name, phone, email)
        self.customers[c.id] = c
        self.save_all()
        return c

    def find_customer_by_name(self, name):
        found = [c.to_dict() for c in self.customers.values() if name.lower() in c.name.lower()]
        return found

    def list_customers(self):
        return [c.to_dict() for c in self.customers.values()]

    # Orders
    def place_order(self, order: Order):
        # Check stock
        for item in order.items:
            pid = item["product_id"]
            qty = item["quantity"]
            if pid not in self.products:
                raise KeyError(f"Produto {pid} não encontrado")
            if self.products[pid].stock < qty:
                raise ValueError(f"Estoque insuficiente para {self.products[pid].name}")
        # Deduct stock
        for item in order.items:
            pid = item["product_id"]
            qty = item["quantity"]
            self.products[pid].stock -= qty

        # Save order
        self.orders[order.id] = order.to_dict()

        # Loyalty points (1 point per currency unit spent, rounded down)
        if order.customer_id and order.customer_id in self.customers:
            pts = int(order.total())
            self.customers[order.customer_id].points += pts

        self.save_all()
        return order

    def get_order(self, order_id):
        return self.orders.get(order_id)

    def daily_sales(self, date_iso=None):
        # Summarize sales per date (YYYY-MM-DD)
        if date_iso is None:
            target = datetime.datetime.now().date().isoformat()
        else:
            target = date_iso.split("T")[0] if "T" in date_iso else date_iso
        total = 0.0
        orders = []
        for o in self.orders.values():
            created = o["created_at"]
            if created.startswith(target):
                orders.append(o)
                total += float(o.get("total", 0))
        return {"date": target, "orders": orders, "total": round(total, 2)}

# --- Small demo runner that creates sample data and performs operations ---
def demo_run(output_path=None):
    sys = CoffeeSystem()

    # Clean initial data for demo (don't erase user's real data if present; only create if empty)
    if not sys.products:
        sys.add_product("Café Expresso", 4.50, 50, "Café espresso curto", "Bebida")
        sys.add_product("Cappuccino", 7.00, 30, "Leite e café", "Bebida")
        sys.add_product("Pão de Queijo", 3.50, 40, "Salgado tradicional", "Salgado")
    if not sys.customers:
        sys.add_customer("Ana Silva", "61999990000", "ana@mail.com")
        sys.add_customer("João Pereira", "61988880000", "joao@mail.com")

    # Create an order for Ana
    cust = list(sys.customers.values())[0]
    order = Order(customer_id=cust.id)
    # pick first product twice and second product once
    products_list = list(sys.products.values())
    order.add_item(products_list[0].id, products_list[0].name, products_list[0].price, 2)
    order.add_item(products_list[1].id, products_list[1].name, products_list[1].price, 1)
    sys.place_order(order)

    # Create a guest order
    order2 = Order(customer_id=None)
    order2.add_item(products_list[2].id, products_list[2].name, products_list[2].price, 3)
    sys.place_order(order2)

    # Prepare demo text output
    lines = []
    lines.append("=== DEMO: Coffee Shops Tia Rosa - Execução de Exemplo ===")
    lines.append("Produtos cadastrados:")
    for p in sys.list_products():
        lines.append(f'  - {p["id"]} | {p["name"]} | R$ {p["price"]:.2f} | Estoque: {p["stock"]}')

    lines.append("")
    lines.append("Clientes cadastrados:")
    for c in sys.list_customers():
        lines.append(f'  - {c["id"]} | {c["name"]} | pontos: {c["points"]}')

    lines.append("")
    lines.append("Pedidos realizados (resumo):")
    for o in sys.orders.values():
        lines.append(f'  - Pedido {o["id"]} | Cliente: {o.get("customer_id")} | Total: R$ {o.get("total"):.2f} | Itens: {len(o["items"])}')

    # Daily sales summary
    sales = sys.daily_sales()
    lines.append("")
    lines.append(f'Vendas do dia {sales["date"]}: total R$ {sales["total"]:.2f} em {len(sales["orders"])} pedidos')

    content = "\n".join(lines)
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
    return content

if __name__ == "__main__":
    import sys as _sys
    if "--demo" in _sys.argv:
        out = demo_run(output_path=os.path.join(DATA_DIR, "demo_output.txt"))
        print(out)
    else:
        # Simple command-line menu (interactive)
        cs = CoffeeSystem()
        menu = """
Coffee Shops Tia Rosa - Sistema
1) Listar produtos
2) Adicionar produto
3) Editar produto (por id)
4) Listar clientes
5) Adicionar cliente
6) Realizar pedido (simples)
7) Ver vendas do dia
0) Sair
"""
        while True:
            print(menu)
            choice = input("Escolha uma opção: ").strip()
            if choice == "1":
                for p in cs.list_products():
                    print(f'{p["id"]} | {p["name"]} | R$ {p["price"]:.2f} | Estoque: {p["stock"]}')
            elif choice == "2":
                name = input("Nome do produto: ").strip()
                price = float(input("Preço (ex: 5.50): ").strip())
                stock = int(input("Estoque inicial: ").strip())
                desc = input("Descrição (opcional): ").strip()
                cat = input("Categoria (opcional): ").strip()
                p = cs.add_product(name, price, stock, desc, cat)
                print(f'Produto criado: {p.id} | {p.name}')
            elif choice == "3":
                pid = input("ID do produto: ").strip()
                if pid not in cs.products:
                    print("Produto não encontrado.")
                    continue
                print("Deixe em branco para não alterar o campo.")
                name = input(f'Nome [{cs.products[pid].name}]: ').strip()
                price = input(f'Preço [{cs.products[pid].price}]: ').strip()
                stock = input(f'Estoque [{cs.products[pid].stock}]: ').strip()
                kwargs = {}
                if name: kwargs["name"] = name
                if price: kwargs["price"] = float(price)
                if stock: kwargs["stock"] = int(stock)
                cs.edit_product(pid, **kwargs)
                print("Produto atualizado.")
            elif choice == "4":
                for c in cs.list_customers():
                    print(f'{c["id"]} | {c["name"]} | pontos: {c["points"]}')
            elif choice == "5":
                name = input("Nome do cliente: ").strip()
                phone = input("Telefone (opcional): ").strip()
                email = input("Email (opcional): ").strip()
                c = cs.add_customer(name, phone, email)
                print(f'Cliente criado: {c.id} | {c.name}')
            elif choice == "6":
                cid = input("ID do cliente (deixe vazio para cliente avulso): ").strip() or None
                order = Order(customer_id=cid)
                print("Adicione itens (digite 'ok' quando terminar):")
                while True:
                    pid = input("ID do produto: ").strip()
                    if pid.lower() == "ok":
                        break
                    if pid not in cs.products:
                        print("Produto não encontrado. Tente novamente.")
                        continue
                    qty = int(input("Quantidade: ").strip())
                    prod = cs.products[pid]
                    order.add_item(pid, prod.name, prod.price, qty)
                    print(f'Item adicionado: {prod.name} x{qty}')
                try:
                    placed = cs.place_order(order)
                    print(f'Pedido realizado: {placed.id} | Total R$ {placed.total():.2f}')
                except Exception as e:
                    print("Erro ao processar pedido:", e)
            elif choice == "7":
                sales = cs.daily_sales()
                print(f'Vendas do dia {sales["date"]}: total R$ {sales["total"]:.2f} em {len(sales["orders"])} pedidos')
            elif choice == "0":
                print("Saindo...")
                break
            else:
                print("Opção inválida. Tente novamente.")
