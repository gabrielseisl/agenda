const $ = (s) => document.querySelector(s);
let modo = "entrar"; // "entrar" ou "criar"

function definirModo(novo) {
  modo = novo;
  const criar = modo === "criar";
  $("#aba-entrar").classList.toggle("ativa", !criar);
  $("#aba-criar").classList.toggle("ativa", criar);
  $("#campo-nome").hidden = !criar;
  $("#campo-confirma").hidden = !criar;
  $("#titulo").textContent = criar ? "Crie sua conta" : "Acesse sua conta";
  $("#subtitulo").textContent = criar
    ? "Preencha os dados abaixo. Leva menos de um minuto."
    : "Informe seu e-mail e senha para continuar.";
  $("#btn-enviar").textContent = criar ? "Criar conta" : "Entrar";
  $("#troca-texto").textContent = criar ? "Já tem uma conta?" : "Ainda não tem conta?";
  $("#troca-link").textContent = criar ? "Entrar" : "Criar conta";
  $("#senha").autocomplete = criar ? "new-password" : "current-password";
  mostrarErro("");
}

function mostrarErro(msg) {
  const e = $("#erro");
  e.textContent = msg;
  e.hidden = !msg;
}

async function enviar(ev) {
  ev.preventDefault();
  mostrarErro("");
  const email = $("#email").value.trim();
  const senha = $("#senha").value;
  let corpo, url;

  if (modo === "criar") {
    const nome = $("#nome").value.trim();
    if (nome.length < 2) return mostrarErro("Informe seu nome.");
    if (senha.length < 6) return mostrarErro("A senha precisa ter pelo menos 6 caracteres.");
    if (senha !== $("#confirma").value) return mostrarErro("As senhas não são iguais.");
    corpo = { nome, email, senha };
    url = "/api/auth/registrar";
  } else {
    if (!email || !senha) return mostrarErro("Informe e-mail e senha.");
    corpo = { email, senha };
    url = "/api/auth/entrar";
  }

  const botao = $("#btn-enviar");
  botao.disabled = true;
  try {
    const resp = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(corpo),
    });
    if (resp.ok) {
      window.location.replace("/");
      return;
    }
    let msg = "Não foi possível concluir. Tente novamente.";
    if (resp.status >= 500) msg = "Erro no servidor. Verifique se o MySQL está ligado.";
    try {
      const j = await resp.json();
      if (typeof j.detail === "string") msg = j.detail;
      else if (Array.isArray(j.detail)) msg = j.detail.map((d) => d.msg.replace(/^Value error, /, "")).join(" ");
    } catch {}
    mostrarErro(msg);
  } catch {
    mostrarErro("Não foi possível falar com o servidor.");
  } finally {
    botao.disabled = false;
  }
}

$("#form").addEventListener("submit", enviar);
$("#aba-entrar").addEventListener("click", () => definirModo("entrar"));
$("#aba-criar").addEventListener("click", () => definirModo("criar"));
$("#troca-link").addEventListener("click", () => definirModo(modo === "entrar" ? "criar" : "entrar"));
$("#ver-senha").addEventListener("click", () => {
  const campo = $("#senha");
  const oculto = campo.type === "password";
  campo.type = oculto ? "text" : "password";
  $("#ver-senha").textContent = oculto ? "Ocultar" : "Mostrar";
});
