class Carrinho:
    def __init__(self, sacola):
        self.sacola = sacola

    def adicionar(self, produto):
        for item in self.sacola:
            if item["id"] == produto[0]:
                item["quantidade"] += 1
                return
        self.sacola.append({
            "id": produto[0],
            "nome": produto[1],
            "valor": produto[2],
            "quantidade": 1
        })

    def remover_item(self, produto_id):
        for item in self.sacola:
            if item["id"] == produto_id:
                item["quantidade"] -= 1
                if item["quantidade"] <= 0:
                    self.sacola.remove(item)
                break

    def excluir_item(self, produto_id):
        self.sacola[:] = [item for item in self.sacola if item["id"] != produto_id]

    def limpar(self):
        self.sacola.clear()
