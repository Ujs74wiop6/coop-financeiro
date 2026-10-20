// Único JavaScript do sistema: confirmação antes de excluir.
// Qualquer <form data-confirmar="texto"> abre o diálogo antes de ser enviado.

let formularioPendente = null;
const dialogo = document.getElementById("dlg-confirma");

if (dialogo) {
  document.addEventListener("submit", (evento) => {
    const mensagem = evento.target.dataset.confirmar;
    if (!mensagem) return;              // formulário comum: segue normalmente
    evento.preventDefault();            // segura o envio até o usuário confirmar
    formularioPendente = evento.target;
    document.getElementById("texto-confirma").textContent = mensagem;
    dialogo.showModal();
  });

  document.getElementById("btn-cancelar").addEventListener("click", () => dialogo.close());

  document.getElementById("btn-confirmar").addEventListener("click", () => {
    dialogo.close();
    formularioPendente.submit();        // .submit() envia sem disparar o evento de novo
  });
}
