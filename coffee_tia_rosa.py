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

# Define o diretório onde os dados serão armazenados
if "__file__" in globals():
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
else:
    # Padrão para o ambiente atual, caso __file__ não esteja definido
    SCRIPT_DIR = os.path.join(os.getcwd(), "coffee_tia_rosa_project")

DATA_DIR = os.path.join(SCRIPT_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)  # Cria o diretório se não existir

# Função para salvar dados em JSON no diretório DATA_DIR
def _save_json(filename, data):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# Função para carregar dados JSON, ou retornar valor padrão se o arquivo não existir
def _load_json(filename, default):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# Classe que representa um produto no sistema
class Product:
    def __init__(self, name: str, price: float, stock: int, description: str = "", category: str = ""):
        self.id = str(uuid.uuid4())[:8]  # Gera um ID único curto para o produto
        self.name = name
        self.price = round(float(price), 2)  # Preço com duas casas decimais
        self.stock = int(stock)  # Quantidade em estoque
        self.description = description
        self.category = category

    # Converte o objeto para dicionário (útil para salvar em JSON)
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "price": self.price,
            "stock": self.stock,
            "description": self.description,
            "category": self.category
        }

    # Cria um objeto Product a partir de um dicionário (ex: carregado do JSON)
    @staticmethod
    def from_dict(d):
        p = Product(d["name"], d["price"], d["stock"], d.get("description",""), d.get("category",""))
        p.id = d["id"]  # Mantém o ID original
        return p

# Classe que representa um cliente
class Customer:
    def __init__(self, name: str, phone: str = "", email: str = ""):
        self.id = str(uuid.uuid4())[:8]  # Gera um ID único curto para o cliente
        self.name = name
        self.phone = phone
        self.email = email
        self.points = 0  # Pontos para programa de fidelidade

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

# Classe que representa um pedido
class Order:
    def __init__(self, customer_id: str = None):
        self.id = str(uuid.uuid4())[:10]  # ID único para o pedido
        self.customer_id = customer_id  # ID do cliente (pode ser None para pedido avulso)
        self.items = []  # Lista de itens: cada item é dict com info do produto, quantidade, subtotal
        self.created_at = datetime.datetime.now().isoformat()  # Timestamp da criação

    # Adiciona um item ao pedido
    def add_item(self, product_id, name, unit_price, qty):
        self.items.append({
            "product_id": product_id,
            "name": name,
            "unit_price": round(unit_price,2),
            "quantity": int(qty),
            "subtotal": round(unit_price * qty, 2)
        })

    # Calcula o valor total do pedido somando subtotais
    def total(self):
        return round(sum(item["subtotal"] for item in self.items), 2)

    # Converte o pedido para dicionário (para salvar)
    def to_dict(self):
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "items": self.items,
            "created_at": self.created_at,
            "total": self.total()
        }

# Classe principal do sistema que gerencia produtos, clientes e pedidos
class CoffeeSystem:
    def __init__(self):
        self.products: Dict[str, Product] = {}  # Dicionário de produtos (key=id)
        self.customers: Dict[str, Customer] = {}  # Dicionário de clientes
        self.orders: Dict[str, Order] = {}  # Dicionário de pedidos
        self.load_all()  # Carrega dados salvos

    # Carrega os dados salvos em JSON para os dicionários
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

    # Salva todos os dados atuais em JSON
    def save_all(self):
        _save_json("products.json", [p.to_dict() for p in self.products.values()])
        _save_json("customers.json", [c.to_dict() for c in self.customers.values()])
        _save_json("orders.json", [o for o in self.orders.values()])

    # Adiciona um produto novo
    def add_product(self, name, price, stock, description="", category=""):
        p = Product(name, price, stock, description, category)
        self.products[p.id] = p
        self.save_all()  # Salva as alterações
        return p

    # Edita um produto existente, passando parâmetros via kwargs (nome, preço, estoque, etc)
    def edit_product(self, product_id, **kwargs):
        if product_id not in self.products:
            raise KeyError("Produto não encontrado")
        p = self.products[product_id]
        for k,v in kwargs.items():
            if hasattr(p, k):
                setattr(p, k, v)
        self.save_all()
        return p

    # Retorna lista de todos produtos (como dicionários)
    def list_products(self):
        return [p.to_dict() for p in self.products.values()]

    # Adiciona um cliente novo
    def add_customer(self, name, phone="", email=""):
        c = Customer(name, phone, email)
        self.customers[c.id] = c
        self.save_all()
        return c

    # Busca clientes por nome (contendo string passada)
    def find_customer_by_name(self, name):
        found = [c.to_dict() for c in self.customers.values() if name.lower() in c.name.lower()]
        return found

    # Retorna lista de todos clientes
    def list_customers(self):
        return [c.to_dict() for c in self.customers.values()]

    # Processa o pedido: verifica estoque, atualiza estoque, salva pedido, adiciona pontos de fidelidade
    def place_order(self, order: Order):
        # Verifica se há estoque suficiente para cada item
        for item in order.items:
            pid = item["product_id"]
            qty = item["quantity"]
            if pid not in self.products:
                raise KeyError(f"Produto {pid} não encontrado")
            if self.products[pid].stock < qty:
                raise ValueError(f"Estoque insuficiente para {self.products[pid].name}")
        # Deduz o estoque dos produtos vendidos
        for item in order.items:
            pid = item["product_id"]
            qty = item["quantity"]
            self.products[pid].stock -= qty

        # Salva o pedido
        self.orders[order.id] = order.to_dict()

        # Atualiza pontos de fidelidade (1 ponto por unidade monetária gasta)
        if order.customer_id and order.customer_id in self.customers:
            pts = int(order.total())
            self.customers[order.customer_id].points += pts

        self.save_all()
        return order

    # Recupera um pedido pelo ID
    def get_order(self, order_id):
        return self.orders.get(order_id)

    # Resumo das vendas do dia
    def daily_sales(self, date_iso=None):
        # Se não informar data, pega data atual
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

# --- Função para executar uma demonstração simples do sistema ---
def demo_run(output_path=None):
    sys = CoffeeSystem()

    # Cria produtos e clientes iniciais caso não existam
    if not sys.products:
        sys.add_product("Café Expresso", 4.50, 50, "Café espresso curto", "Bebida")
        sys.add_product("Cappuccino", 7.00, 30, "Leite e café", "Bebida")
        sys.add_product("Pão de Queijo", 3.50, 40, "Salgado tradicional", "Salgado")
    if not sys.customers:
        sys.add_customer("Ana Silva", "61999990000", "ana@mail.com")
        sys.add_customer("João Pereira", "61988880000", "joao@mail.com")

    # Cria pedido para Ana com 2 cafés e 1 cappuccino
    cust = list(sys.customers.values())[0]
    order = Order(customer_id=cust.id)
    products_list = list(sys.products.values())
    order.add_item(products_list[0].id, products_list[0].name, products_list[0].price, 2)
    order.add_item(products_list[1].id, products_list[1].name, products_list[1].price, 1)
    sys.place_order(order)

    # Pedido de convidado (sem cliente)
    order2 = Order(customer_id=None)
    order2.add_item(products_list[2].id, products_list[2].name, products_list[2].price, 3)
    sys.place_order(order2)

    # Gera saída textual para demonstração
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

    sales = sys.daily_sales()
    lines.append("")
    lines.append(f'Vendas do dia {sales["date"]}: total R$ {sales["total"]:.2f} em {len(sales["orders"])} pedidos')

    content = "\n".join(lines)
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
    return content

# --- Menu interativo simples para usar o sistema via linha de comando ---
if __name__ == "__main__":
    import sys as _sys
    if "--demo" in _sys.argv:
        out = demo_run(output_path=os.path.join(DATA_DIR, "demo_output.txt"))
        print(out)
    else:
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
                # Listar produtos cadastrados
                for p in cs.list_products():
                    print(f'{p["id"]} | {p["name"]} | R$ {p["price"]:.2f} | Estoque: {p["stock"]}')
            elif choice == "2":
                # Adicionar novo produto
                name = input("Nome do produto: ").strip()
                price = float(input("Preço (ex: 5.50): ").strip())
                stock = int(input("Estoque inicial: ").strip())
                desc = input("Descrição (opcional): ").strip()
                cat = input("Categoria (opcional): ").strip()
                p = cs.add_product(name, price, stock, desc, cat)
                print(f'Produto criado: {p.id} | {p.name}')
            elif choice == "3":
                # Editar produto pelo ID
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
                # Listar clientes cadastrados
                for c in cs.list_customers():
                    print(f'{c["id"]} | {c["name"]} | pontos: {c["points"]}')
            elif choice == "5":
                # Adicionar cliente novo
                name = input("Nome do cliente: ").strip()
                phone = input("Telefone (opcional): ").strip()
                email = input("Email (opcional): ").strip()
                c = cs.add_customer(name, phone, email)
                print(f'Cliente criado: {c.id} | {c.name}')
            elif choice == "6":
                # Realizar pedido simples
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
                # Exibe resumo das vendas do dia atual
                sales = cs.daily_sales()
                print(f'Vendas do dia {sales["date"]}: total R$ {sales["total"]:.2f} em {len(sales["orders"])} pedidos')
            elif choice == "0":
                print("Saindo...")
                break
            else:
                print("Opção inválida. Tente novamente.")
              
