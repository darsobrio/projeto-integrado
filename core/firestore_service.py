from core import db

def salvar_usuario_firestore(usuario):
    """Salva ou atualiza os dados do usuário no Firestore."""

    uid = usuario.firebase_uid

    if not uid:
        raise ValueError(
            "O usuário ainda não possui um UID do Firebase."
        )

    dados = {
        "firebase_uid": uid,
        "email": usuario.email,
        "nome_completo": usuario.nome_completo or "",
        "tipo_usuario": usuario.tipo_usuario,
        "cidade": usuario.cidade or "",
        "telefone": usuario.telefone or "",
    }
    db.collection("usuarios").document(uid).set(
        dados,
        merge=True,
    )
    return uid
def buscar_usuario_firestore(uid):
    """Busca um usuário pelo UID do Firebase."""
    documento = (
        db.collection("usuarios")
        .document(uid)
        .get())
    if not documento.exists:
        return None
    return documento.to_dict()
def excluir_usuario_firestore(uid):
    """Exclui o documento do usuário no Firestore."""
    db.collection("usuarios").document(uid).delete()
def testar_gravacao_firestore():
    """Cria um documento de teste no Firestore."""
    documento = db.collection("_testes").document("conexao_oportunet")
    documento.set({
        "status": "conectado",
        "projeto": "Oportunet",})
    resultado = documento.get()
    return resultado.exists