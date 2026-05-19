import streamlit as st
import pandas as pd
import json, os
from datetime import datetime, date
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Power Financeiro", page_icon="⚡", layout="wide")

DATA_FILE = os.path.join(os.path.dirname(__file__), "data.json")

st.markdown("""
<style>
.card{background:var(--background-color);border:1px solid #e2e8f0;border-radius:14px;padding:18px;text-align:center;margin-bottom:4px}
.card-label{font-size:11px;color:#64748b;font-weight:700;text-transform:uppercase;letter-spacing:.6px;margin-bottom:6px}
.card-value{font-size:24px;font-weight:700;margin-bottom:2px}
.card-sub{font-size:11px;color:#94a3b8}
.green{color:#0f6e56}.red{color:#c0392b}.blue{color:#185fa5}.amber{color:#ba7517}.purple{color:#6c3483}
.tag{display:inline-block;padding:2px 9px;border-radius:20px;font-size:11px;font-weight:600}
.tag-entrada{background:#d5f5e3;color:#0f6e56}
.tag-saida{background:#fadbd8;color:#a32d2d}
.tag-transf{background:#d6e4f7;color:#185fa5}
.tag-pendente{background:#faeeda;color:#ba7517}
.tag-recebido{background:#d5f5e3;color:#0f6e56}
.lanc-row{display:flex;align-items:center;gap:12px;padding:10px 14px;border:1px solid #e2e8f0;border-radius:10px;margin-bottom:6px}
.section-title{font-size:15px;font-weight:700;color:#1e293b;margin:16px 0 10px 0;display:flex;align-items:center;gap:8px}
.alert-info{background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;padding:10px 14px;font-size:13px;color:#1d4ed8;margin-bottom:14px}
.resumo-box{background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:12px;margin-top:8px}
.stButton>button{border-radius:8px}
[data-testid="stSidebarNav"]{display:none}
</style>
""", unsafe_allow_html=True)

# ─── PERFIS ───────────────────────────────────────────────────────────────────
PERFIS = {
    "Admin":      {"painel":True, "lancar":True, "extrato":True, "orcamentos":True, "completar_orc":True, "rescisoes":True, "fluxo":True, "config":True},
    "Socio":      {"painel":True, "lancar":False,"extrato":True, "orcamentos":True, "completar_orc":True, "rescisoes":True, "fluxo":True, "config":False},
    "Operacional":{"painel":True, "lancar":True, "extrato":True, "orcamentos":False,"completar_orc":False,"rescisoes":True, "fluxo":True, "config":False},
    "RDO":        {"painel":False,"lancar":False,"extrato":False,"orcamentos":True, "completar_orc":False,"rescisoes":False,"fluxo":False,"config":False},
    "Bloqueado":  {"painel":False,"lancar":False,"extrato":False,"orcamentos":False,"completar_orc":False,"rescisoes":False,"fluxo":False,"config":False},
}

def pode(perfil, acao):
    return PERFIS.get(perfil, {}).get(acao, False)

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
            "sicredi":{"nome":"Sicredi Power","saldo":0.0},
            "itau":   {"nome":"Deivid Itaú",  "saldo":0.0},
            "gilmar": {"nome":"Conta Gilmar",  "saldo":0.0},
        },
        "lancamentos":[
            {"id":1,"data":"19/05/2026","tipo":"Entrada","conta":"sicredi",
             "categoria":"Nota fiscal recebida","empresa":"Power Eletric",
             "beneficiario":"Cliente ABC Indústria",
             "descricao":"Nota #0047 - Serviços elétricos",
             "valor":69000.0,"lancado_por":"Alessandra","obs":""}
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
            "Rescisão","Férias","Despesas pessoais","Hotel / Hospedagem",
            "Manutenção veículo","FGTS / Encargos","Outros"],
        "usuarios":{
            "alessandra":{"senha":"power123","perfil":"Admin",      "nome":"Alessandra"},
            "gilmar":    {"senha":"power123","perfil":"Socio",      "nome":"Gilmar"},
            "elisangela":{"senha":"power123","perfil":"Socio",      "nome":"Elisangela"},
            "deivid":    {"senha":"power123","perfil":"Operacional","nome":"Deivid"},
            "thiago":    {"senha":"power123","perfil":"RDO",        "nome":"Thiago"},
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
    s = float(D["contas"][conta_id]["saldo"])
    for l in D["lancamentos"]:
        if l["conta"] == conta_id:
            if l["tipo"] == "Entrada": s += l["valor"]
            elif l["tipo"] in ("Saída","Transferência"): s -= l["valor"]
        if l.get("conta_destino") == conta_id and l["tipo"] == "Transferência":
            s += l["valor"]
    return s

# ─── LOGIN ────────────────────────────────────────────────────────────────────
if not st.session_state.usuario:
    st.markdown("<br><br>",unsafe_allow_html=True)
    _,col,_ = st.columns([1,1.2,1])
    with col:
        st.markdown("## ⚡ Power Financeiro")
        st.markdown("##### Sistema de gestão financeira")
        st.markdown("Power Eletric &nbsp;·&nbsp; Power Equipamentos")
        st.markdown("---")
        login = st.text_input("Usuário", placeholder="seu login").strip().lower()
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar", use_container_width=True, type="primary"):
            u = D["usuarios"].get(login)
            if u and u["senha"] == senha:
                if u["perfil"] == "Bloqueado":
                    st.error("Você não tem acesso ao sistema.")
                else:
                    st.session_state.usuario = login
                    st.rerun()
            else:
                st.error("Usuário ou senha incorretos")
        st.caption("Fale com a Alessandra para recuperar sua senha")
    st.stop()

u    = D["usuarios"][st.session_state.usuario]
perf = u["perfil"]

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚡ Power Financeiro")
    st.markdown(f"**{u['nome']}** · {perf}")
    st.markdown("---")
    menus = []
    if pode(perf,"painel"):      menus.append("📊 Painel")
    if pode(perf,"lancar"):      menus.append("➕ Lançar")
    if pode(perf,"extrato"):     menus.append("📋 Extrato")
    if pode(perf,"orcamentos"):  menus.append("📄 Orçamentos")
    if pode(perf,"rescisoes"):   menus.append("👥 Rescisões")
    if pode(perf,"fluxo"):       menus.append("💰 Fluxo de Caixa")
    if pode(perf,"config"):      menus.append("⚙️ Configurações")
    aba = st.radio("Menu", menus, label_visibility="collapsed")
    st.markdown("---")
    if st.button("Sair", use_container_width=True):
        st.session_state.usuario = None
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PAINEL
# ══════════════════════════════════════════════════════════════════════════════
if aba == "📊 Painel":
    st.markdown(f"## 📊 Painel Geral &nbsp;<span style='font-size:13px;color:#94a3b8;font-weight:400'>{datetime.now().strftime('%d/%m/%Y %H:%M')}</span>", unsafe_allow_html=True)

    s_sic = saldo_conta("sicredi")
    s_ita = saldo_conta("itau")
    s_gil = saldo_conta("gilmar")
    a_rec = sum(o["valor"] for o in D["orcamentos"] if o.get("status_rec","Pendente")=="Pendente")
    n_rec = len([o for o in D["orcamentos"] if o.get("status_rec","Pendente")=="Pendente"])
    resc  = sum(max(r["valor_total"]-r["valor_pago"],0) for r in D["rescisoes"])
    total_e = sum(l["valor"] for l in D["lancamentos"] if l["tipo"]=="Entrada")
    total_s = sum(l["valor"] for l in D["lancamentos"] if l["tipo"]=="Saída")

    # ── CARDS PRINCIPAIS ──────────────────────────────────────────────────────
    c1,c2,c3,c4,c5 = st.columns(5)
    cards = [
        (c1, "Sicredi Power",    s_sic, "green" if s_sic>=0 else "red", "Conta principal"),
        (c2, "Deivid Itaú",      s_ita, "green" if s_ita>=0 else "red", "Despesas / pagamentos"),
        (c3, "A Receber",        a_rec, "blue",   f"{n_rec} orçamentos pendentes"),
        (c4, "Entradas (total)", total_e,"green", "Todos os lançamentos"),
        (c5, "Rescisões Abertas",resc,  "red",    "Saldo a pagar"),
    ]
    for col,label,val,cor,sub in cards:
        with col:
            st.markdown(f'<div class="card"><div class="card-label">{label}</div><div class="card-value {cor}">{fmt(val)}</div><div class="card-sub">{sub}</div></div>',unsafe_allow_html=True)

    st.markdown("<br>",unsafe_allow_html=True)

    # ── CONTA GILMAR — RESUMO MENSAL ──────────────────────────────────────────
    mes_atual = datetime.now().strftime("%m/%Y")
    gil_ent = sum(l["valor"] for l in D["lancamentos"] if l["tipo"]=="Entrada" and l["conta"]=="gilmar" and l["data"].endswith(mes_atual.replace("/","/")))
    gil_sai = sum(l["valor"] for l in D["lancamentos"] if l["tipo"]=="Saída"   and l["conta"]=="gilmar" and l["data"].endswith(mes_atual.replace("/","/")))

    st.markdown(f"""
    <div style="background:#f4ecf7;border:1px solid #d7bde2;border-radius:12px;padding:12px 18px;margin-bottom:16px;display:flex;align-items:center;gap:24px">
      <div><span style="font-size:12px;color:#6c3483;font-weight:700">📋 CONTA GILMAR — RESUMO {mes_atual}</span></div>
      <div><span style="font-size:12px;color:#64748b">Entrou:</span> <span style="font-weight:700;color:#0f6e56">{fmt(gil_ent)}</span></div>
      <div><span style="font-size:12px;color:#64748b">Saiu:</span> <span style="font-weight:700;color:#c0392b">{fmt(gil_sai)}</span></div>
      <div><span style="font-size:12px;color:#64748b">Saldo mês:</span> <span style="font-weight:700;color:#6c3483">{fmt(gil_ent-gil_sai)}</span></div>
    </div>""", unsafe_allow_html=True)

    col_a,col_b = st.columns([1.6,1])

    with col_a:
        st.markdown('<div class="section-title">🕐 Últimos lançamentos</div>',unsafe_allow_html=True)
        lancs = sorted(D["lancamentos"],key=lambda x:x["id"],reverse=True)[:12]
        if lancs:
            for l in lancs:
                tipo  = l["tipo"]
                ctag  = "entrada" if tipo=="Entrada" else "saida" if tipo=="Saída" else "transf"
                sinal = "+" if tipo=="Entrada" else "↔" if tipo=="Transferência" else "-"
                cval  = "#0f6e56" if tipo=="Entrada" else "#185fa5" if tipo=="Transferência" else "#c0392b"
                cnome = D["contas"].get(l["conta"],{}).get("nome",l["conta"])
                st.markdown(f"""
                <div class="lanc-row">
                  <span class="tag tag-{ctag}">{tipo}</span>
                  <div style="flex:1;min-width:0">
                    <div style="font-size:13px;font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{l['beneficiario']}</div>
                    <div style="font-size:11px;color:#64748b">{l['data']} · {cnome} · {l['categoria']}</div>
                  </div>
                  <div style="font-weight:700;color:{cval};white-space:nowrap">{sinal} {fmt(l['valor'])}</div>
                </div>""",unsafe_allow_html=True)
        else:
            st.info("Nenhum lançamento ainda. Use ➕ Lançar para começar!")

    with col_b:
        st.markdown('<div class="section-title">📊 Orçamentos por cliente</div>',unsafe_allow_html=True)
        orcs_p = [o for o in D["orcamentos"] if o.get("status_rec","Pendente")=="Pendente"]
        if orcs_p:
            df_c = pd.DataFrame(orcs_p).groupby("cliente")["valor"].sum().reset_index()
            df_c = df_c.sort_values("valor",ascending=False).head(8)
            fig = px.bar(df_c,x="valor",y="cliente",orientation="h",
                        color_discrete_sequence=["#185fa5"],labels={"valor":"R$","cliente":""})
            fig.update_layout(margin=dict(l=0,r=0,t=5,b=0),height=230,
                             plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)")
            fig.update_xaxes(showgrid=True,gridcolor="#f0f0f0",tickformat=",.0f")
            fig.update_yaxes(showgrid=False)
            st.plotly_chart(fig,use_container_width=True)

        st.markdown('<div class="section-title">⚠️ Rescisões em aberto</div>',unsafe_allow_html=True)
        for r in D["rescisoes"]:
            sr = r["valor_total"]-r["valor_pago"]
            if sr > 0:
                pct = int(r["valor_pago"]/r["valor_total"]*100) if r["valor_total"] else 0
                st.markdown(f"""
                <div style="padding:8px 10px;border:1px solid #e2e8f0;border-radius:8px;margin-bottom:5px">
                  <div style="display:flex;justify-content:space-between;margin-bottom:3px">
                    <span style="font-size:13px;font-weight:600">{r['funcionario']}</span>
                    <span style="font-size:12px;color:#c0392b;font-weight:700">{fmt(sr)}</span>
                  </div>
                  <div style="height:5px;background:#f1f5f9;border-radius:4px">
                    <div style="height:5px;background:#185fa5;border-radius:4px;width:{pct}%"></div>
                  </div>
                  <div style="font-size:10px;color:#94a3b8;margin-top:2px">{pct}% pago de {fmt(r['valor_total'])}</div>
                </div>""",unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# LANÇAR
# ══════════════════════════════════════════════════════════════════════════════
elif aba == "➕ Lançar":
    st.markdown("## ➕ Novo Lançamento")
    tipo = st.radio("Tipo",["Entrada","Saída","Transferência"],horizontal=True)
    col1,col2 = st.columns(2)
    with col1:
        data_l = st.date_input("Data",value=date.today())
        valor  = st.number_input("Valor (R$)",min_value=0.01,step=0.01,format="%.2f")
        contas_disp = {k:v for k,v in {c:D["contas"][c]["nome"] for c in D["contas"]}.items()
                       if not (perf=="Operacional" and k=="gilmar")}
        conta = st.selectbox("Conta",options=list(contas_disp.keys()),format_func=lambda x:contas_disp[x])
        if tipo=="Transferência":
            dest = {k:v for k,v in contas_disp.items() if k!=conta}
            conta_dest = st.selectbox("Conta destino",options=list(dest.keys()),format_func=lambda x:dest[x])
        else:
            conta_dest = None
    with col2:
        categoria    = st.selectbox("Categoria",D["categorias"])
        empresa      = st.selectbox("Empresa",["Power Eletric","Power Equipamentos","Casa","Pessoal / Sócio","Geral"])
        beneficiario = st.text_input("Beneficiário / Origem")
        st.info(f"Será lançado por: **{u['nome']}**")
    descricao = st.text_area("Descrição / Observação",height=80)

    if st.button("✅ Confirmar Lançamento",type="primary",use_container_width=True):
        if valor<=0: st.error("Informe um valor válido")
        elif not beneficiario: st.error("Informe o beneficiário")
        else:
            nid = max([l["id"] for l in D["lancamentos"]],default=0)+1
            D["lancamentos"].append({
                "id":nid,"data":data_l.strftime("%d/%m/%Y"),
                "tipo":tipo,"conta":conta,"conta_destino":conta_dest,
                "categoria":categoria,"empresa":empresa,
                "beneficiario":beneficiario,"descricao":descricao,
                "valor":float(valor),"lancado_por":u["nome"],
            })
            salvar()
            st.success(f"✅ {fmt(valor)} lançado com sucesso!")
            st.rerun()

    if perf=="Admin":
        st.markdown("---")
        st.markdown("#### 🏦 Saldo inicial das contas")
        st.caption("Defina o saldo de abertura de cada conta")
        c1,c2,c3 = st.columns(3)
        for cid,col in zip(["sicredi","itau","gilmar"],[c1,c2,c3]):
            with col:
                ns = st.number_input(D["contas"][cid]["nome"],value=float(D["contas"][cid]["saldo"]),step=0.01,format="%.2f",key=f"s_{cid}")
                if st.button("Salvar",key=f"b_{cid}"):
                    D["contas"][cid]["saldo"]=ns; salvar(); st.success("Salvo!")

# ══════════════════════════════════════════════════════════════════════════════
# EXTRATO
# ══════════════════════════════════════════════════════════════════════════════
elif aba == "📋 Extrato":
    st.markdown("## 📋 Extrato de Lançamentos")
    col1,col2,col3 = st.columns(3)
    fc = col1.selectbox("Conta",["Todas"]+[D["contas"][c]["nome"] for c in D["contas"]])
    ft = col2.selectbox("Tipo",["Todos","Entrada","Saída","Transferência"])
    fcat=col3.selectbox("Categoria",["Todas"]+D["categorias"])

    lancs = D["lancamentos"].copy()
    if fc!="Todas":
        cid=next(c for c in D["contas"] if D["contas"][c]["nome"]==fc)
        lancs=[l for l in lancs if l["conta"]==cid or l.get("conta_destino")==cid]
    if ft!="Todos":  lancs=[l for l in lancs if l["tipo"]==ft]
    if fcat!="Todas":lancs=[l for l in lancs if l["categoria"]==fcat]
    lancs=sorted(lancs,key=lambda x:x["id"],reverse=True)

    te=sum(l["valor"] for l in lancs if l["tipo"]=="Entrada")
    ts=sum(l["valor"] for l in lancs if l["tipo"]=="Saída")
    c1,c2,c3=st.columns(3)
    c1.metric("Entradas",fmt(te))
    c2.metric("Saídas",fmt(ts))
    c3.metric("Saldo período",fmt(te-ts))
    st.markdown("---")

    for l in lancs:
        tipo=l["tipo"]
        ctag="entrada" if tipo=="Entrada" else "saida" if tipo=="Saída" else "transf"
        sinal="+" if tipo=="Entrada" else "↔" if tipo=="Transferência" else "-"
        cval="#0f6e56" if tipo=="Entrada" else "#185fa5" if tipo=="Transferência" else "#c0392b"
        cnome=D["contas"].get(l["conta"],{}).get("nome",l["conta"])
        with st.expander(f"{l['data']}  |  {l['beneficiario']}  |  {sinal} {fmt(l['valor'])}"):
            c1,c2,c3=st.columns(3)
            c1.write(f"**Tipo:** {tipo}")
            c1.write(f"**Categoria:** {l['categoria']}")
            c2.write(f"**Conta:** {cnome}")
            c2.write(f"**Empresa:** {l.get('empresa','—')}")
            c3.write(f"**Lançado por:** {l.get('lancado_por','—')}")
            c3.write(f"**Descrição:** {l.get('descricao','—')}")
            if perf=="Admin":
                if st.button("🗑️ Excluir",key=f"del_{l['id']}"):
                    D["lancamentos"]=[x for x in D["lancamentos"] if x["id"]!=l["id"]]
                    salvar(); st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# ORÇAMENTOS
# ══════════════════════════════════════════════════════════════════════════════
elif aba == "📄 Orçamentos":
    st.markdown("## 📄 Orçamentos e Notas a Receber")
    tab1,tab2,tab3 = st.tabs(["📋 Lista","➕ Novo RDO / Orçamento","✏️ Completar (NF / Recebimento)"])

    with tab1:
        c1,c2,c3=st.columns(3)
        fcli =c1.selectbox("Cliente",["Todos"]+sorted(set(o["cliente"] for o in D["orcamentos"])))
        fresp=c2.selectbox("Responsável",["Todos"]+sorted(set(o["responsavel"] for o in D["orcamentos"])))
        fst  =c3.selectbox("Status",["Todos","Pendente","Recebido"])

        orcs=D["orcamentos"].copy()
        if fcli!="Todos":  orcs=[o for o in orcs if o["cliente"]==fcli]
        if fresp!="Todos": orcs=[o for o in orcs if o["responsavel"]==fresp]
        if fst!="Todos":   orcs=[o for o in orcs if o.get("status_rec","Pendente")==fst]

        tp=sum(o["valor"] for o in orcs if o.get("status_rec","Pendente")=="Pendente")
        tr=sum(o["valor"] for o in orcs if o.get("status_rec","")=="Recebido")
        c1,c2,c3=st.columns(3)
        c1.metric("Listados",len(orcs))
        c2.metric("Pendente",fmt(tp))
        c3.metric("Recebido",fmt(tr))
        st.markdown("---")

        for o in orcs:
            st_rec=o.get("status_rec","Pendente")
            tag="🟡" if st_rec=="Pendente" else "✅"
            with st.expander(f"{tag} Orç. {o['num']} | {o['cliente']} | {fmt(o['valor'])} | {o['responsavel']}"):
                c1,c2=st.columns(2)
                c1.write(f"**Serviço:** {o['servico']}")
                c1.write(f"**Nota Fiscal:** {o.get('n_nf','—')}")
                c1.write(f"**Pedido Compra:** {o.get('n_ped','—')}")
                c2.write(f"**Previsão recebimento:** {o.get('prev_rec','—')}")
                c2.write(f"**Status:** {st_rec}")
                c2.write(f"**Obs:** {o.get('obs','—')}")

    with tab2:
        st.markdown("#### Novo RDO / Orçamento")
        st.caption("Thiago e Elisangela podem lançar aqui")
        c1,c2=st.columns(2)
        with c1:
            nn  =st.text_input("Número do orçamento")
            nc  =st.text_input("Cliente")
            nr  =st.text_input("Responsável / Supervisor")
            ns_ =st.text_area("Descrição do serviço",height=80)
            ncolab=st.text_area("Colaboradores envolvidos",height=60,placeholder="Ex: Alex Medeiros, Roeder Santos")
        with c2:
            nv  =st.number_input("Valor (R$)",min_value=0.0,step=0.01,format="%.2f")
            ndt =st.date_input("Data do serviço",value=date.today())
            nemp=st.selectbox("Empresa",["Power Eletric","Power Equipamentos"])
            nobs=st.text_area("Observações",height=60)
        if st.button("✅ Cadastrar",type="primary"):
            if not nc or not ns_:
                st.error("Preencha cliente e serviço")
            else:
                nid=max([o["id"] for o in D["orcamentos"]],default=0)+1
                D["orcamentos"].append({
                    "id":nid,"num":nn,"cliente":nc,"responsavel":nr,
                    "servico":ns_,"colaboradores":ncolab,"valor":float(nv),
                    "data_serv":ndt.strftime("%d/%m/%Y"),"empresa":nemp,
                    "prev_rec":"","n_nf":"","n_ped":"",
                    "status_rec":"Pendente","obs":nobs,
                    "lancado_por":u["nome"]
                })
                salvar(); st.success("Orçamento cadastrado!"); st.rerun()

    with tab3:
        if not pode(perf,"completar_orc"):
            st.warning("Apenas Elisangela, Alessandra ou Gilmar podem completar os orçamentos.")
        else:
            st.markdown("#### Completar orçamento — NF, Pedido de Compra e Recebimento")
            st.caption("Esta aba é para Elisangela / Alessandra finalizarem os dados")
            pendentes_comp=[o for o in D["orcamentos"] if not o.get("n_nf") or o.get("status_rec","Pendente")=="Pendente"]
            if not pendentes_comp:
                st.success("Todos os orçamentos estão completos!")
            for o in pendentes_comp:
                with st.expander(f"Orç. {o['num']} | {o['cliente']} | {fmt(o['valor'])}"):
                    c1,c2,c3=st.columns(3)
                    nnf2 =c1.text_input("Nota Fiscal",value=o.get("n_nf",""),key=f"nf_{o['id']}")
                    nped2=c2.text_input("Pedido de Compra",value=o.get("n_ped",""),key=f"ped_{o['id']}")
                    nprev=c3.text_input("Previsão recebimento",value=o.get("prev_rec",""),key=f"prev_{o['id']}")
                    nst2 =st.selectbox("Status recebimento",["Pendente","Recebido"],
                                       index=0 if o.get("status_rec","Pendente")=="Pendente" else 1,
                                       key=f"st2_{o['id']}")
                    nobs2=st.text_input("Obs",value=o.get("obs",""),key=f"obs2_{o['id']}")
                    if st.button("💾 Salvar",key=f"save2_{o['id']}"):
                        for oo in D["orcamentos"]:
                            if oo["id"]==o["id"]:
                                oo["n_nf"]=nnf2; oo["n_ped"]=nped2
                                oo["prev_rec"]=nprev; oo["status_rec"]=nst2
                                oo["obs"]=nobs2
                                if nst2=="Recebido": oo["dt_recebimento"]=date.today().strftime("%d/%m/%Y")
                        salvar(); st.success("Salvo!"); st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# RESCISÕES
# ══════════════════════════════════════════════════════════════════════════════
elif aba == "👥 Rescisões":
    st.markdown("## 👥 Controle de Rescisões")
    tab1,tab2=st.tabs(["📋 Em aberto","➕ Nova rescisão"])
    with tab1:
        total_ab=sum(max(r["valor_total"]-r["valor_pago"],0) for r in D["rescisoes"])
        st.metric("Total em aberto",fmt(total_ab))
        st.markdown("---")
        for r in D["rescisoes"]:
            sr=r["valor_total"]-r["valor_pago"]
            pct=int(r["valor_pago"]/r["valor_total"]*100) if r["valor_total"] else 0
            with st.expander(f"{r['funcionario']} | Saldo: {fmt(sr)} | {pct}% pago"):
                c1,c2,c3=st.columns(3)
                c1.write(f"**Desligamento:** {r.get('dt_deslig','—')}")
                c1.write(f"**Total rescisão:** {fmt(r['valor_total'])}")
                c2.write(f"**Total pago:** {fmt(r['valor_pago'])}")
                c2.write(f"**Saldo em aberto:** {fmt(sr)}")
                c3.write(f"**Pendências:** {r.get('obs','—')}")
                st.progress(pct/100)
                if perf=="Admin":
                    npag=st.number_input("Registrar pagamento (R$)",min_value=0.0,step=0.01,format="%.2f",key=f"p_{r['id']}")
                    if st.button("Registrar",key=f"bp_{r['id']}"):
                        for rr in D["rescisoes"]:
                            if rr["id"]==r["id"]: rr["valor_pago"]=round(rr["valor_pago"]+npag,2)
                        salvar(); st.success("Pagamento registrado!"); st.rerun()
    with tab2:
        if perf!="Admin": st.warning("Apenas Admin pode registrar rescisões")
        else:
            c1,c2=st.columns(2)
            with c1:
                nrf=st.text_input("Funcionário")
                nrd=st.date_input("Data desligamento")
                nrt=st.number_input("Valor total rescisão (R$)",min_value=0.01,step=0.01,format="%.2f")
            with c2:
                nrp=st.number_input("Valor já pago (R$)",min_value=0.0,step=0.01,format="%.2f")
                nro=st.text_area("Pendências (FGTS, multa, verbas...)",height=100)
            if st.button("✅ Registrar rescisão",type="primary"):
                if not nrf or nrt<=0: st.error("Preencha nome e valor")
                else:
                    nid=max([r["id"] for r in D["rescisoes"]],default=0)+1
                    D["rescisoes"].append({"id":nid,"funcionario":nrf,
                        "dt_deslig":nrd.strftime("%d/%m/%Y"),
                        "valor_total":float(nrt),"valor_pago":float(nrp),"obs":nro})
                    salvar(); st.success("Rescisão registrada!"); st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# FLUXO DE CAIXA
# ══════════════════════════════════════════════════════════════════════════════
elif aba == "💰 Fluxo de Caixa":
    st.markdown("## 💰 Fluxo de Caixa")
    if not D["lancamentos"]:
        st.info("Nenhum lançamento registrado ainda.")
    else:
        df=pd.DataFrame(D["lancamentos"])
        te=sum(l["valor"] for l in D["lancamentos"] if l["tipo"]=="Entrada")
        ts=sum(l["valor"] for l in D["lancamentos"] if l["tipo"]=="Saída")
        c1,c2,c3=st.columns(3)
        c1.metric("Total entradas",fmt(te))
        c2.metric("Total saídas",fmt(ts))
        c3.metric("Saldo geral",fmt(te-ts),delta=f"R$ {te-ts:,.0f}".replace(",","."))

        col_a,col_b=st.columns(2)
        with col_a:
            st.markdown("#### Saídas por categoria")
            dfs=df[df["tipo"]=="Saída"].groupby("categoria")["valor"].sum().reset_index()
            if not dfs.empty:
                fig=px.pie(dfs,values="valor",names="categoria",
                          color_discrete_sequence=px.colors.sequential.Blues_r,hole=0.4)
                fig.update_layout(margin=dict(l=0,r=0,t=10,b=0),height=300,
                                 paper_bgcolor="rgba(0,0,0,0)",showlegend=True)
                st.plotly_chart(fig,use_container_width=True)
            else: st.info("Nenhuma saída lançada")
        with col_b:
            st.markdown("#### Entradas por categoria")
            dfe=df[df["tipo"]=="Entrada"].groupby("categoria")["valor"].sum().reset_index()
            if not dfe.empty:
                fig2=px.pie(dfe,values="valor",names="categoria",
                           color_discrete_sequence=px.colors.sequential.Greens_r,hole=0.4)
                fig2.update_layout(margin=dict(l=0,r=0,t=10,b=0),height=300,
                                  paper_bgcolor="rgba(0,0,0,0)",showlegend=True)
                st.plotly_chart(fig2,use_container_width=True)
            else: st.info("Nenhuma entrada lançada")

        st.markdown("---")
        st.markdown("#### 🔍 Rastrear — onde foi o dinheiro?")
        busca=st.text_input("Digite nome, nota, cliente ou descrição")
        if busca:
            res=[l for l in D["lancamentos"] if busca.lower() in l.get("beneficiario","").lower()
                 or busca.lower() in l.get("descricao","").lower()
                 or busca.lower() in l.get("categoria","").lower()]
            if res:
                be=sum(l["valor"] for l in res if l["tipo"]=="Entrada")
                bs=sum(l["valor"] for l in res if l["tipo"]=="Saída")
                c1,c2,c3=st.columns(3)
                c1.metric("Entradas",fmt(be))
                c2.metric("Saídas",fmt(bs))
                c3.metric("Saldo",fmt(be-bs))
                for l in res:
                    tipo=l["tipo"]
                    sinal="+" if tipo=="Entrada" else "↔" if tipo=="Transferência" else "-"
                    cval="#0f6e56" if tipo=="Entrada" else "#185fa5" if tipo=="Transferência" else "#c0392b"
                    cnome=D["contas"].get(l["conta"],{}).get("nome",l["conta"])
                    st.markdown(f"""
                    <div class="lanc-row">
                      <span class="tag tag-{'entrada' if tipo=='Entrada' else 'saida' if tipo=='Saída' else 'transf'}">{tipo}</span>
                      <div style="flex:1">
                        <div style="font-size:13px;font-weight:600">{l['beneficiario']}</div>
                        <div style="font-size:11px;color:#64748b">{l['data']} · {cnome} · {l.get('descricao','')}</div>
                      </div>
                      <div style="font-weight:700;color:{cval}">{sinal} {fmt(l['valor'])}</div>
                    </div>""",unsafe_allow_html=True)
            else: st.warning("Nenhum lançamento encontrado")

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÕES
# ══════════════════════════════════════════════════════════════════════════════
elif aba == "⚙️ Configurações":
    st.markdown("## ⚙️ Configurações")
    tab1,tab2,tab3=st.tabs(["👥 Usuários","🏷️ Categorias","🏦 Contas"])

    with tab1:
        st.markdown("#### Usuários do sistema")
        perfis_disp=["Admin","Socio","Operacional","RDO","Bloqueado"]
        for uid,uu in D["usuarios"].items():
            with st.expander(f"{uu['nome']} · {uu['perfil']}"):
                c1,c2,c3=st.columns(3)
                nn2=c1.text_input("Nome",value=uu["nome"],key=f"un_{uid}")
                np2=c2.selectbox("Perfil",perfis_disp,index=perfis_disp.index(uu["perfil"]) if uu["perfil"] in perfis_disp else 0,key=f"up_{uid}")
                ns2=c3.text_input("Nova senha",type="password",placeholder="deixe vazio para não alterar",key=f"us_{uid}")
                if st.button("Salvar",key=f"ub_{uid}"):
                    D["usuarios"][uid]["nome"]=nn2
                    D["usuarios"][uid]["perfil"]=np2
                    if ns2: D["usuarios"][uid]["senha"]=ns2
                    salvar(); st.success("Salvo!")

    with tab2:
        st.markdown("#### Categorias de lançamento")
        st.caption("Adicione ou remova categorias conforme necessário")
        for i,c in enumerate(D["categorias"]):
            c1,c2=st.columns([5,1])
            c1.write(f"• {c}")
            if c2.button("🗑️",key=f"dc_{i}"):
                D["categorias"].pop(i); salvar(); st.rerun()
        st.markdown("---")
        ncat=st.text_input("Nova categoria")
        if st.button("➕ Adicionar categoria",type="primary"):
            if ncat and ncat not in D["categorias"]:
                D["categorias"].append(ncat); salvar()
                st.success(f"'{ncat}' adicionada!"); st.rerun()
            elif ncat in D["categorias"]:
                st.warning("Categoria já existe")

    with tab3:
        st.markdown("#### Contas bancárias")
        for cid in D["contas"]:
            cc=D["contas"][cid]
            with st.expander(cc["nome"]):
                nn3=st.text_input("Nome da conta",value=cc["nome"],key=f"cn_{cid}")
                if st.button("Salvar nome",key=f"cb_{cid}"):
                    D["contas"][cid]["nome"]=nn3; salvar(); st.success("Salvo!")
