import streamlit as st
import pandas as pd
import json, os
from datetime import datetime, date
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Power Financeiro", page_icon="⚡", layout="wide")

DATA_FILE = os.path.join(os.path.dirname(__file__), "data.json")

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.metric-card{background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:16px;text-align:center}
.metric-label{font-size:12px;color:#64748b;font-weight:600;text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px}
.metric-value{font-size:24px;font-weight:700}
.green{color:#0f6e56}.red{color:#c0392b}.blue{color:#185fa5}.amber{color:#ba7517}
.tag{display:inline-block;padding:2px 8px;border-radius:6px;font-size:11px;font-weight:600}
.tag-pendente{background:#faeeda;color:#ba7517}
.tag-recebido{background:#d5f5e3;color:#0f6e56}
.tag-entrada{background:#d5f5e3;color:#0f6e56}
.tag-saida{background:#fadbd8;color:#a32d2d}
.tag-transf{background:#d6e4f7;color:#185fa5}
.tag-aberto{background:#faeeda;color:#ba7517}
.tag-pago{background:#d5f5e3;color:#0f6e56}
.tag-vencido{background:#fadbd8;color:#a32d2d}
.stButton>button{border-radius:8px}
div[data-testid="stSidebarNav"]{display:none}
</style>
""", unsafe_allow_html=True)

# ─── DATA ─────────────────────────────────────────────────────────────────────
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE,"r",encoding="utf-8") as f:
            return json.load(f)
    return build_default()

def save_data(d):
    with open(DATA_FILE,"w",encoding="utf-8") as f:
        json.dump(d,f,ensure_ascii=False,indent=2,default=str)

def build_default():
    orc_file = os.path.join(os.path.dirname(__file__),"pendentes.json")
    orcs = json.load(open(orc_file,encoding="utf-8")) if os.path.exists(orc_file) else []
    return {
        "contas":{
            "sicredi":{"nome":"Sicredi Power","saldo":0.0,"cor":"#185fa5"},
            "itau":   {"nome":"Deivid Itaú",  "saldo":0.0,"cor":"#ba7517"},
            "gilmar": {"nome":"Conta Gilmar", "saldo":0.0,"cor":"#6c3483"},
        },
        "lancamentos":[
            {"id":1,"data":"19/05/2026","tipo":"Entrada","conta":"sicredi","categoria":"Nota fiscal recebida",
             "beneficiario":"Cliente ABC Indústria","descricao":"Nota #0047 - Serviços elétricos",
             "valor":69000.0,"lancado_por":"Gilmar","obs":""}
        ],
        "orcamentos": orcs,
        "rescisoes":[
            {"id":1,"funcionario":"Maikon","dt_deslig":"08/07/2025","valor_total":12168.82,"valor_pago":2000.0,"obs":"FGTS + multa pendentes"},
            {"id":2,"funcionario":"Nilton","dt_deslig":"03/12/2025","valor_total":9786.39,"valor_pago":1957.27,"obs":"FGTS pendente"},
            {"id":3,"funcionario":"Agnaldo","dt_deslig":"03/12/2025","valor_total":22515.0,"valor_pago":4503.0,"obs":"FGTS + multa pendentes"},
            {"id":4,"funcionario":"Celso","dt_deslig":"03/12/2025","valor_total":14005.44,"valor_pago":2801.08,"obs":"FGTS pendente"},
            {"id":5,"funcionario":"Pabolo","dt_deslig":"17/06/2025","valor_total":16897.76,"valor_pago":9000.0,"obs":"Parcelas em aberto"},
            {"id":6,"funcionario":"Alessandro","dt_deslig":"22/08/2025","valor_total":9346.79,"valor_pago":7009.85,"obs":"Saldo final pendente"},
        ],
        "categorias":["Folha de pagamento","Adiantamento","Vale mercado","Alimentação",
            "Combustível","Material","Boleto / Fornecedor","Nota fiscal recebida",
            "Movimentação bancária","Impostos","Medicina do trabalho","Empréstimo",
            "Rescisão","Férias","Despesas pessoais","Outros"],
        "usuarios":{
            "gilmar":    {"senha":"power123","perfil":"Admin","nome":"Gilmar"},
            "alessandra":{"senha":"power123","perfil":"Financeiro","nome":"Alessandra"},
            "deivid":    {"senha":"power123","perfil":"Operacional","nome":"Deivid"},
            "usuario4":  {"senha":"power123","perfil":"Lançador","nome":"Usuário 4"},
            "usuario5":  {"senha":"power123","perfil":"Lançador","nome":"Usuário 5"},
        }
    }

if "data" not in st.session_state:
    st.session_state.data = load_data()
if "usuario" not in st.session_state:
    st.session_state.usuario = None

D = st.session_state.data

def salvar():
    save_data(st.session_state.data)
    st.session_state.data = load_data()

def fmt(v):
    if v is None: return "—"
    return f"R$ {v:,.2f}".replace(",","X").replace(".",",").replace("X",".")

def saldo_conta(conta_id):
    s = D["contas"][conta_id]["saldo"]
    for l in D["lancamentos"]:
        if l["conta"] == conta_id:
            if l["tipo"] == "Entrada": s += l["valor"]
            elif l["tipo"] == "Saída": s -= l["valor"]
        if l.get("conta_destino") == conta_id and l["tipo"] == "Transferência":
            s += l["valor"]
        if l["conta"] == conta_id and l["tipo"] == "Transferência":
            s -= l["valor"]
    return s

# ─── LOGIN ─────────────────────────────────────────────────────────────────────
if not st.session_state.usuario:
    st.markdown("<br>",unsafe_allow_html=True)
    col1,col2,col3 = st.columns([1,1.2,1])
    with col2:
        st.markdown("## ⚡ Power Financeiro")
        st.markdown("Sistema de gestão financeira")
        st.markdown("---")
        login = st.text_input("Usuário",placeholder="seu login").strip().lower()
        senha = st.text_input("Senha",type="password")
        if st.button("Entrar",use_container_width=True,type="primary"):
            u = D["usuarios"].get(login)
            if u and u["senha"] == senha:
                st.session_state.usuario = login
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos")
        st.caption("Contato: admin do sistema para recuperar senha")
    st.stop()

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
u = D["usuarios"][st.session_state.usuario]
with st.sidebar:
    st.markdown(f"### ⚡ Power Financeiro")
    st.markdown(f"**{u['nome']}** · {u['perfil']}")
    st.markdown("---")
    aba = st.radio("Navegação", [
        "📊 Painel",
        "➕ Lançar",
        "📋 Extrato",
        "📄 Orçamentos",
        "👥 Funcionários / Rescisões",
        "💰 Fluxo de Caixa",
        "⚙️ Configurações",
    ], label_visibility="collapsed")
    st.markdown("---")
    if st.button("Sair",use_container_width=True):
        st.session_state.usuario = None
        st.rerun()

perfil = u["perfil"]

# ══════════════════════════════════════════════════════════════════════════════
# PAINEL
# ══════════════════════════════════════════════════════════════════════════════
if aba == "📊 Painel":
    st.markdown("## 📊 Painel Geral")
    st.caption(f"Atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    # Saldos
    s_sicredi = saldo_conta("sicredi")
    s_itau    = saldo_conta("itau")
    s_gilmar  = saldo_conta("gilmar")

    # A receber
    a_receber = sum(o["valor"] for o in D["orcamentos"] if o.get("status_rec","Pendente") == "Pendente")

    # Rescisões em aberto
    rescisoes_abertas = sum(max(r["valor_total"]-r["valor_pago"],0) for r in D["rescisoes"])

    col1,col2,col3,col4,col5 = st.columns(5)
    with col1:
        cor = "green" if s_sicredi>=0 else "red"
        st.markdown(f'<div class="metric-card"><div class="metric-label">Sicredi Power</div><div class="metric-value {cor}">{fmt(s_sicredi)}</div></div>',unsafe_allow_html=True)
    with col2:
        cor = "green" if s_itau>=0 else "red"
        st.markdown(f'<div class="metric-card"><div class="metric-label">Deivid Itaú</div><div class="metric-value {cor}">{fmt(s_itau)}</div></div>',unsafe_allow_html=True)
    with col3:
        cor = "green" if s_gilmar>=0 else "red"
        st.markdown(f'<div class="metric-card"><div class="metric-label">Conta Gilmar</div><div class="metric-value {cor}">{fmt(s_gilmar)}</div></div>',unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-card"><div class="metric-label">A Receber (Orç.)</div><div class="metric-value blue">{fmt(a_receber)}</div></div>',unsafe_allow_html=True)
    with col5:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Rescisões Abertas</div><div class="metric-value red">{fmt(rescisoes_abertas)}</div></div>',unsafe_allow_html=True)

    st.markdown("<br>",unsafe_allow_html=True)

    # Gráfico por categoria
    col_a, col_b = st.columns([1.5,1])
    with col_a:
        st.markdown("#### Últimos lançamentos")
        lancs = sorted(D["lancamentos"], key=lambda x: x["id"], reverse=True)[:15]
        if lancs:
            for l in lancs:
                tipo = l["tipo"]
                cor_tag = "entrada" if tipo=="Entrada" else "saida" if tipo=="Saída" else "transf"
                sinal = "+" if tipo=="Entrada" else ("↔" if tipo=="Transferência" else "-")
                cor_val = "green" if tipo=="Entrada" else ("blue" if tipo=="Transferência" else "red")
                conta_nome = D["contas"].get(l["conta"],{}).get("nome",l["conta"])
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:12px;padding:8px;border:1px solid #e2e8f0;border-radius:8px;margin-bottom:6px;background:#fafafa">
                  <span class="tag tag-{cor_tag}">{tipo}</span>
                  <div style="flex:1">
                    <div style="font-size:13px;font-weight:600">{l['beneficiario']}</div>
                    <div style="font-size:11px;color:#64748b">{l['data']} · {conta_nome} · {l['categoria']}</div>
                  </div>
                  <div style="font-weight:700;color:{'#0f6e56' if cor_val=='green' else '#185fa5' if cor_val=='blue' else '#c0392b'}">{sinal} {fmt(l['valor'])}</div>
                </div>""",unsafe_allow_html=True)
        else:
            st.info("Nenhum lançamento ainda. Use ➕ Lançar para começar!")

    with col_b:
        st.markdown("#### Orçamentos pendentes por cliente")
        orcs_pend = [o for o in D["orcamentos"] if o.get("status_rec","Pendente")=="Pendente"]
        if orcs_pend:
            df_cli = pd.DataFrame(orcs_pend).groupby("cliente")["valor"].sum().reset_index()
            df_cli = df_cli.sort_values("valor",ascending=False)
            fig = px.bar(df_cli,x="valor",y="cliente",orientation="h",
                        color_discrete_sequence=["#185fa5"],
                        labels={"valor":"Valor (R$)","cliente":"Cliente"})
            fig.update_layout(margin=dict(l=0,r=0,t=10,b=0),height=300,
                             plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)")
            fig.update_xaxes(showgrid=True,gridcolor="#f0f0f0")
            fig.update_yaxes(showgrid=False)
            st.plotly_chart(fig,use_container_width=True)

        # Rescisões rápido
        st.markdown("#### Rescisões em aberto")
        for r in D["rescisoes"]:
            saldo_r = r["valor_total"] - r["valor_pago"]
            if saldo_r > 0:
                pct = int(r["valor_pago"]/r["valor_total"]*100) if r["valor_total"] else 0
                st.markdown(f"""
                <div style="padding:7px;border:1px solid #e2e8f0;border-radius:8px;margin-bottom:5px">
                  <div style="display:flex;justify-content:space-between">
                    <span style="font-size:13px;font-weight:600">{r['funcionario']}</span>
                    <span style="font-size:12px;color:#c0392b;font-weight:600">{fmt(saldo_r)}</span>
                  </div>
                  <div style="height:4px;background:#f0f0f0;border-radius:4px;margin-top:5px">
                    <div style="height:4px;background:#185fa5;border-radius:4px;width:{pct}%"></div>
                  </div>
                  <div style="font-size:10px;color:#94a3b8;margin-top:2px">{pct}% pago de {fmt(r['valor_total'])}</div>
                </div>""",unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# LANÇAR
# ══════════════════════════════════════════════════════════════════════════════
elif aba == "➕ Lançar":
    st.markdown("## ➕ Novo Lançamento")

    tipo = st.radio("Tipo de lançamento",["Entrada","Saída","Transferência"],horizontal=True)

    col1,col2 = st.columns(2)
    with col1:
        data_l = st.date_input("Data",value=date.today())
        valor  = st.number_input("Valor (R$)",min_value=0.01,step=0.01,format="%.2f")
        conta_opts = {cid: D["contas"][cid]["nome"] for cid in D["contas"]}
        conta = st.selectbox("Conta",options=list(conta_opts.keys()),format_func=lambda x:conta_opts[x])
        if tipo=="Transferência":
            conta_dest_opts = {cid: D["contas"][cid]["nome"] for cid in D["contas"] if cid!=conta}
            conta_dest = st.selectbox("Conta destino",options=list(conta_dest_opts.keys()),format_func=lambda x:conta_dest_opts[x])
        else:
            conta_dest = None
    with col2:
        categoria = st.selectbox("Categoria",D["categorias"])
        empresa   = st.selectbox("Empresa",["Power Eletric","Power Equipamentos","Casa","Pessoal / Sócio","Geral"])
        beneficiario = st.text_input("Beneficiário / Origem")
        lancado_por  = st.selectbox("Lançado por",[D["usuarios"][uid]["nome"] for uid in D["usuarios"]])

    descricao = st.text_area("Descrição / Observação",height=80)

    if st.button("✅ Confirmar Lançamento",type="primary",use_container_width=True):
        if valor <= 0:
            st.error("Informe um valor válido")
        elif not beneficiario:
            st.error("Informe o beneficiário")
        else:
            novo_id = max([l["id"] for l in D["lancamentos"]],default=0)+1
            novo = {
                "id": novo_id,
                "data": data_l.strftime("%d/%m/%Y"),
                "tipo": tipo,
                "conta": conta,
                "conta_destino": conta_dest,
                "categoria": categoria,
                "empresa": empresa,
                "beneficiario": beneficiario,
                "descricao": descricao,
                "valor": float(valor),
                "lancado_por": lancado_por,
            }
            D["lancamentos"].append(novo)
            salvar()
            st.success(f"✅ Lançamento de {fmt(valor)} registrado com sucesso!")
            st.rerun()

    # Ajuste de saldo inicial
    st.markdown("---")
    st.markdown("#### Ajustar saldo inicial das contas")
    st.caption("Use para corrigir o saldo de abertura de cada conta")
    col1,col2,col3 = st.columns(3)
    for idx,(cid,col) in enumerate(zip(["sicredi","itau","gilmar"],[col1,col2,col3])):
        with col:
            novo_saldo = st.number_input(
                D["contas"][cid]["nome"],
                value=float(D["contas"][cid]["saldo"]),
                step=0.01,format="%.2f",key=f"saldo_{cid}")
            if st.button(f"Salvar",key=f"btn_{cid}"):
                D["contas"][cid]["saldo"] = novo_saldo
                salvar()
                st.success("Salvo!")

# ══════════════════════════════════════════════════════════════════════════════
# EXTRATO
# ══════════════════════════════════════════════════════════════════════════════
elif aba == "📋 Extrato":
    st.markdown("## 📋 Extrato de Lançamentos")

    col1,col2,col3 = st.columns(3)
    with col1:
        filtro_conta = st.selectbox("Conta",["Todas"]+[D["contas"][c]["nome"] for c in D["contas"]])
    with col2:
        filtro_tipo  = st.selectbox("Tipo",["Todos","Entrada","Saída","Transferência"])
    with col3:
        filtro_cat   = st.selectbox("Categoria",["Todas"]+D["categorias"])

    lancs = D["lancamentos"].copy()
    if filtro_conta != "Todas":
        cid = next(c for c in D["contas"] if D["contas"][c]["nome"]==filtro_conta)
        lancs = [l for l in lancs if l["conta"]==cid or l.get("conta_destino")==cid]
    if filtro_tipo != "Todos":
        lancs = [l for l in lancs if l["tipo"]==filtro_tipo]
    if filtro_cat != "Todas":
        lancs = [l for l in lancs if l["categoria"]==filtro_cat]

    lancs = sorted(lancs,key=lambda x:x["id"],reverse=True)

    total_e = sum(l["valor"] for l in lancs if l["tipo"]=="Entrada")
    total_s = sum(l["valor"] for l in lancs if l["tipo"]=="Saída")
    saldo_f = total_e - total_s

    c1,c2,c3 = st.columns(3)
    c1.metric("Total entradas",fmt(total_e))
    c2.metric("Total saídas",fmt(total_s))
    c3.metric("Saldo período",fmt(saldo_f),delta=f"{saldo_f:+.2f}")

    st.markdown("---")

    for l in lancs:
        tipo  = l["tipo"]
        ctag  = "entrada" if tipo=="Entrada" else "saida" if tipo=="Saída" else "transf"
        sinal = "+" if tipo=="Entrada" else ("↔" if tipo=="Transferência" else "-")
        cval  = "#0f6e56" if tipo=="Entrada" else "#185fa5" if tipo=="Transferência" else "#c0392b"
        cnome = D["contas"].get(l["conta"],{}).get("nome",l["conta"])
        cdest = ""
        if l.get("conta_destino"):
            cdest = f" → {D['contas'].get(l['conta_destino'],{}).get('nome',l['conta_destino'])}"
        with st.expander(f"{l['data']}  |  {l['beneficiario']}  |  {sinal} {fmt(l['valor'])}",expanded=False):
            col1,col2,col3 = st.columns(3)
            col1.write(f"**Tipo:** {tipo}")
            col1.write(f"**Categoria:** {l['categoria']}")
            col2.write(f"**Conta:** {cnome}{cdest}")
            col2.write(f"**Empresa:** {l.get('empresa','—')}")
            col3.write(f"**Lançado por:** {l.get('lancado_por','—')}")
            col3.write(f"**Descrição:** {l.get('descricao','—')}")
            if perfil in ("Admin","Financeiro"):
                if st.button("🗑️ Excluir lançamento",key=f"del_{l['id']}"):
                    D["lancamentos"] = [x for x in D["lancamentos"] if x["id"]!=l["id"]]
                    salvar()
                    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# ORÇAMENTOS
# ══════════════════════════════════════════════════════════════════════════════
elif aba == "📄 Orçamentos":
    st.markdown("## 📄 Orçamentos e Notas a Receber")

    tab1,tab2 = st.tabs(["📋 Lista de orçamentos","➕ Novo orçamento"])

    with tab1:
        col1,col2,col3 = st.columns(3)
        filtro_cli   = col1.selectbox("Cliente",["Todos"]+sorted(set(o["cliente"] for o in D["orcamentos"])))
        filtro_resp  = col2.selectbox("Responsável",["Todos"]+sorted(set(o["responsavel"] for o in D["orcamentos"])))
        filtro_st    = col3.selectbox("Status",["Todos","Pendente","Recebido"])

        orcs = D["orcamentos"].copy()
        if filtro_cli  != "Todos": orcs = [o for o in orcs if o["cliente"]==filtro_cli]
        if filtro_resp != "Todos": orcs = [o for o in orcs if o["responsavel"]==filtro_resp]
        if filtro_st   != "Todos": orcs = [o for o in orcs if o.get("status_rec","Pendente")==filtro_st]

        total_pend = sum(o["valor"] for o in orcs if o.get("status_rec","Pendente")=="Pendente")
        total_rec  = sum(o["valor"] for o in orcs if o.get("status_rec","")=="Recebido")

        c1,c2,c3 = st.columns(3)
        c1.metric("Orçamentos listados",len(orcs))
        c2.metric("Total pendente",fmt(total_pend))
        c3.metric("Total recebido",fmt(total_rec))
        st.markdown("---")

        for o in orcs:
            st_rec = o.get("status_rec","Pendente")
            tag = "pendente" if st_rec=="Pendente" else "recebido"
            with st.expander(f"Orç. {o['num']} | {o['cliente']} | {fmt(o['valor'])} | {st_rec}"):
                col1,col2 = st.columns(2)
                col1.write(f"**Responsável:** {o['responsavel']}")
                col1.write(f"**Serviço:** {o['servico']}")
                col1.write(f"**Nota Fiscal:** {o.get('n_nf','—')}")
                col2.write(f"**Previsão recebimento:** {o.get('prev_rec','—')}")
                col2.write(f"**Pedido de compra:** {o.get('n_ped','—')}")
                col2.write(f"**Obs:** {o.get('obs','—')}")
                if perfil in ("Admin","Financeiro"):
                    novo_st = st.selectbox("Alterar status",["Pendente","Recebido"],
                                           index=0 if st_rec=="Pendente" else 1,
                                           key=f"st_{o['id']}")
                    if st.button("Salvar status",key=f"save_st_{o['id']}"):
                        for oo in D["orcamentos"]:
                            if oo["id"]==o["id"]:
                                oo["status_rec"]=novo_st
                                if novo_st=="Recebido":
                                    oo["dt_recebimento"]=date.today().strftime("%d/%m/%Y")
                        salvar()
                        st.success("Status atualizado!")
                        st.rerun()

    with tab2:
        st.markdown("#### Cadastrar novo orçamento")
        col1,col2 = st.columns(2)
        with col1:
            n_num   = st.text_input("Número do orçamento")
            n_cli   = st.text_input("Cliente")
            n_resp  = st.text_input("Responsável")
            n_serv  = st.text_area("Descrição do serviço",height=80)
        with col2:
            n_valor = st.number_input("Valor (R$)",min_value=0.01,step=0.01,format="%.2f")
            n_prev  = st.date_input("Previsão de recebimento",value=None)
            n_nf    = st.text_input("Número da nota fiscal")
            n_ped   = st.text_input("Pedido de compra")
            n_obs   = st.text_input("Observação")

        if st.button("✅ Cadastrar orçamento",type="primary"):
            if not n_cli or not n_serv or n_valor<=0:
                st.error("Preencha cliente, serviço e valor")
            else:
                novo_id = max([o["id"] for o in D["orcamentos"]],default=0)+1
                D["orcamentos"].append({
                    "id":novo_id,"num":n_num,"cliente":n_cli,"responsavel":n_resp,
                    "servico":n_serv,"valor":float(n_valor),
                    "prev_rec":n_prev.strftime("%d/%m/%Y") if n_prev else "",
                    "n_nf":n_nf,"n_ped":n_ped,"status_rec":"Pendente","obs":n_obs
                })
                salvar()
                st.success("Orçamento cadastrado!")
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# FUNCIONÁRIOS / RESCISÕES
# ══════════════════════════════════════════════════════════════════════════════
elif aba == "👥 Funcionários / Rescisões":
    st.markdown("## 👥 Controle de Rescisões")

    tab1,tab2 = st.tabs(["📋 Rescisões abertas","➕ Nova rescisão"])

    with tab1:
        total_aberto = sum(max(r["valor_total"]-r["valor_pago"],0) for r in D["rescisoes"])
        st.metric("Total em aberto",fmt(total_aberto))
        st.markdown("---")

        for r in D["rescisoes"]:
            saldo_r = r["valor_total"] - r["valor_pago"]
            pct = int(r["valor_pago"]/r["valor_total"]*100) if r["valor_total"] else 0
            tag = "pago" if saldo_r<=0 else "vencido"
            with st.expander(f"{r['funcionario']} | Saldo: {fmt(saldo_r)} | {pct}% pago"):
                col1,col2,col3 = st.columns(3)
                col1.write(f"**Desligamento:** {r.get('dt_deslig','—')}")
                col1.write(f"**Valor total rescisão:** {fmt(r['valor_total'])}")
                col2.write(f"**Total pago:** {fmt(r['valor_pago'])}")
                col2.write(f"**Saldo em aberto:** {fmt(saldo_r)}")
                col3.write(f"**Obs / Pendências:** {r.get('obs','—')}")
                st.progress(pct/100)

                if perfil in ("Admin","Financeiro"):
                    novo_pago = st.number_input("Registrar novo pagamento (R$)",
                                                min_value=0.0,step=0.01,format="%.2f",key=f"pag_{r['id']}")
                    if st.button("Registrar pagamento",key=f"btn_pag_{r['id']}"):
                        for rr in D["rescisoes"]:
                            if rr["id"]==r["id"]:
                                rr["valor_pago"] = round(rr["valor_pago"]+novo_pago,2)
                        salvar()
                        st.success("Pagamento registrado!")
                        st.rerun()

    with tab2:
        st.markdown("#### Registrar nova rescisão")
        col1,col2 = st.columns(2)
        with col1:
            nr_func   = st.text_input("Nome do funcionário")
            nr_desl   = st.date_input("Data de desligamento")
            nr_total  = st.number_input("Valor total da rescisão (R$)",min_value=0.01,step=0.01,format="%.2f")
        with col2:
            nr_pago   = st.number_input("Valor já pago (R$)",min_value=0.0,step=0.01,format="%.2f")
            nr_obs    = st.text_area("Pendências (FGTS, multa, verbas...)",height=100)

        if st.button("✅ Registrar rescisão",type="primary"):
            if not nr_func or nr_total<=0:
                st.error("Preencha nome e valor")
            else:
                novo_id = max([r["id"] for r in D["rescisoes"]],default=0)+1
                D["rescisoes"].append({
                    "id":novo_id,"funcionario":nr_func,
                    "dt_deslig":nr_desl.strftime("%d/%m/%Y"),
                    "valor_total":float(nr_total),
                    "valor_pago":float(nr_pago),
                    "obs":nr_obs
                })
                salvar()
                st.success("Rescisão registrada!")
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# FLUXO DE CAIXA
# ══════════════════════════════════════════════════════════════════════════════
elif aba == "💰 Fluxo de Caixa":
    st.markdown("## 💰 Fluxo de Caixa")

    if not D["lancamentos"]:
        st.info("Nenhum lançamento registrado ainda.")
    else:
        df = pd.DataFrame(D["lancamentos"])

        # Resumo por categoria
        col1,col2 = st.columns(2)
        with col1:
            st.markdown("#### Saídas por categoria")
            df_saida = df[df["tipo"]=="Saída"].groupby("categoria")["valor"].sum().reset_index()
            if not df_saida.empty:
                df_saida = df_saida.sort_values("valor",ascending=False)
                fig = px.pie(df_saida,values="valor",names="categoria",
                             color_discrete_sequence=px.colors.sequential.Blues_r)
                fig.update_layout(margin=dict(l=0,r=0,t=10,b=0),height=320,
                                  paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig,use_container_width=True)
            else:
                st.info("Nenhuma saída lançada")

        with col2:
            st.markdown("#### Entradas por categoria")
            df_ent = df[df["tipo"]=="Entrada"].groupby("categoria")["valor"].sum().reset_index()
            if not df_ent.empty:
                fig2 = px.pie(df_ent,values="valor",names="categoria",
                              color_discrete_sequence=px.colors.sequential.Greens_r)
                fig2.update_layout(margin=dict(l=0,r=0,t=10,b=0),height=320,
                                   paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig2,use_container_width=True)
            else:
                st.info("Nenhuma entrada lançada")

        # Tabela completa
        st.markdown("#### Todos os lançamentos")
        df_show = df[["data","tipo","beneficiario","categoria","valor","conta","lancado_por"]].copy()
        df_show["conta"] = df_show["conta"].map({c:D["contas"][c]["nome"] for c in D["contas"]})
        df_show["valor"] = df_show["valor"].apply(lambda x: f"R$ {x:,.2f}".replace(",","X").replace(".",",").replace("X","."))
        df_show.columns = ["Data","Tipo","Beneficiário","Categoria","Valor","Conta","Lançado por"]
        st.dataframe(df_show,use_container_width=True,hide_index=True)

        # Rastreamento por nota
        st.markdown("---")
        st.markdown("#### 🔍 Rastrear lançamentos de uma nota")
        busca = st.text_input("Digite parte do nome ou descrição para filtrar")
        if busca:
            resultado = [l for l in D["lancamentos"]
                        if busca.lower() in l.get("beneficiario","").lower()
                        or busca.lower() in l.get("descricao","").lower()]
            if resultado:
                total_e = sum(l["valor"] for l in resultado if l["tipo"]=="Entrada")
                total_s = sum(l["valor"] for l in resultado if l["tipo"]=="Saída")
                st.metric("Entradas",fmt(total_e))
                st.metric("Saídas",fmt(total_s))
                st.metric("Saldo",fmt(total_e-total_s))
                for l in resultado:
                    tipo=l["tipo"]
                    sinal="+" if tipo=="Entrada" else "↔" if tipo=="Transferência" else "-"
                    st.markdown(f"**{l['data']}** · {tipo} · {l['beneficiario']} · {sinal}{fmt(l['valor'])} · _{l.get('descricao','')}_")
            else:
                st.warning("Nenhum lançamento encontrado")

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÕES
# ══════════════════════════════════════════════════════════════════════════════
elif aba == "⚙️ Configurações":
    if perfil != "Admin":
        st.error("Acesso restrito a administradores")
        st.stop()

    st.markdown("## ⚙️ Configurações")
    tab1,tab2,tab3 = st.tabs(["👥 Usuários","🏷️ Categorias","🏦 Contas"])

    with tab1:
        st.markdown("#### Usuários do sistema")
        for uid,u in D["usuarios"].items():
            with st.expander(f"{u['nome']} · {u['perfil']}"):
                col1,col2,col3 = st.columns(3)
                novo_nome  = col1.text_input("Nome",value=u["nome"],key=f"nome_{uid}")
                novo_perf  = col2.selectbox("Perfil",["Admin","Financeiro","Operacional","Lançador"],
                                            index=["Admin","Financeiro","Operacional","Lançador"].index(u["perfil"]),
                                            key=f"perf_{uid}")
                nova_senha = col3.text_input("Nova senha (deixe vazio para não alterar)",
                                             type="password",key=f"senha_{uid}")
                if st.button("Salvar",key=f"save_u_{uid}"):
                    D["usuarios"][uid]["nome"]  = novo_nome
                    D["usuarios"][uid]["perfil"] = novo_perf
                    if nova_senha: D["usuarios"][uid]["senha"] = nova_senha
                    salvar()
                    st.success("Salvo!")

    with tab2:
        st.markdown("#### Categorias de lançamento")
        cats = D["categorias"]
        for i,c in enumerate(cats):
            col1,col2 = st.columns([5,1])
            col1.write(f"• {c}")
            if col2.button("🗑️",key=f"del_cat_{i}"):
                D["categorias"].pop(i); salvar(); st.rerun()
        st.markdown("---")
        nova_cat = st.text_input("Nova categoria")
        if st.button("Adicionar categoria"):
            if nova_cat and nova_cat not in D["categorias"]:
                D["categorias"].append(nova_cat); salvar()
                st.success(f"Categoria '{nova_cat}' adicionada!"); st.rerun()

    with tab3:
        st.markdown("#### Contas bancárias")
        for cid in D["contas"]:
            c = D["contas"][cid]
            with st.expander(c["nome"]):
                novo_nome = st.text_input("Nome da conta",value=c["nome"],key=f"cname_{cid}")
                if st.button("Salvar nome",key=f"save_c_{cid}"):
                    D["contas"][cid]["nome"] = novo_nome; salvar(); st.success("Salvo!")
