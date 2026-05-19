import streamlit as st
import pandas as pd
import json, os
from datetime import datetime, date, timedelta
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Power Financeiro", page_icon="⚡", layout="wide")
DATA_FILE = os.path.join(os.path.dirname(__file__), "data.json")

st.markdown("""
<style>
.card{background:var(--background-color);border:1px solid #e2e8f0;border-radius:14px;padding:16px;text-align:center;margin-bottom:4px}
.card-label{font-size:11px;color:#64748b;font-weight:700;text-transform:uppercase;letter-spacing:.6px;margin-bottom:5px}
.card-value{font-size:22px;font-weight:700;margin-bottom:2px}
.card-sub{font-size:11px;color:#94a3b8}
.green{color:#0f6e56}.red{color:#c0392b}.blue{color:#185fa5}.amber{color:#ba7517}.purple{color:#6c3483}
.tag{display:inline-block;padding:2px 9px;border-radius:20px;font-size:11px;font-weight:600}
.tag-entrada{background:#d5f5e3;color:#0f6e56}
.tag-saida{background:#fadbd8;color:#a32d2d}
.tag-transf{background:#d6e4f7;color:#185fa5}
.tag-pendente{background:#faeeda;color:#ba7517}
.tag-recebido{background:#d5f5e3;color:#0f6e56}
.tag-vencido{background:#fadbd8;color:#a32d2d}
.tag-aberto{background:#faeeda;color:#ba7517}
.tag-pago{background:#d5f5e3;color:#0f6e56}
.lanc-row{display:flex;align-items:center;gap:12px;padding:10px 14px;border:1px solid #e2e8f0;border-radius:10px;margin-bottom:6px}
.section-title{font-size:15px;font-weight:700;color:#1e293b;margin:16px 0 10px 0}
.alert-box{border-radius:10px;padding:10px 16px;margin-bottom:12px;font-size:13px}
.alert-red{background:#fef2f2;border:1px solid #fecaca;color:#991b1b}
.alert-amber{background:#fffbeb;border:1px solid #fde68a;color:#92400e}
.alert-green{background:#f0fdf4;border:1px solid #bbf7d0;color:#166534}
.alert-blue{background:#eff6ff;border:1px solid #bfdbfe;color:#1d4ed8}
.stButton>button{border-radius:8px}
</style>
""", unsafe_allow_html=True)

PERFIS = {
    "Admin":      {"painel":True,"lancar":True,"extrato":True,"orcamentos":True,"completar_orc":True,"contas_pagar":True,"agenda":True,"relatorio":True,"config":True},
    "Socio":      {"painel":True,"lancar":False,"extrato":True,"orcamentos":True,"completar_orc":True,"contas_pagar":True,"agenda":True,"relatorio":True,"config":False},
    "Operacional":{"painel":True,"lancar":True,"extrato":True,"orcamentos":False,"completar_orc":False,"contas_pagar":True,"agenda":True,"relatorio":True,"config":False},
    "RDO":        {"painel":False,"lancar":False,"extrato":False,"orcamentos":True,"completar_orc":False,"contas_pagar":False,"agenda":False,"relatorio":False,"config":False},
    "Bloqueado":  {"painel":False,"lancar":False,"extrato":False,"orcamentos":False,"completar_orc":False,"contas_pagar":False,"agenda":False,"relatorio":False,"config":False},
}

def pode(perfil, acao):
    return PERFIS.get(perfil,{}).get(acao,False)

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
             "beneficiario":"Cliente ABC Indústria","descricao":"Nota #0047 - Serviços elétricos",
             "valor":69000.0,"lancado_por":"Alessandra"}
        ],
        "orcamentos": orcs,
        "contas_pagar":[],
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

def saldo_conta(cid):
    s = float(D["contas"][cid]["saldo"])
    for l in D["lancamentos"]:
        if l["conta"]==cid:
            if l["tipo"]=="Entrada": s+=l["valor"]
            elif l["tipo"] in ("Saída","Transferência"): s-=l["valor"]
        if l.get("conta_destino")==cid and l["tipo"]=="Transferência": s+=l["valor"]
    return s

def parse_date(s):
    try: return datetime.strptime(s,"%d/%m/%Y").date()
    except: return None

# ── LOGIN ─────────────────────────────────────────────────────────────────────
if not st.session_state.usuario:
    st.markdown("<br><br>",unsafe_allow_html=True)
    _,col,_ = st.columns([1,1.2,1])
    with col:
        st.markdown("## ⚡ Power Financeiro")
        st.markdown("##### Sistema de gestão financeira")
        st.markdown("Power Eletric &nbsp;·&nbsp; Power Equipamentos")
        st.markdown("---")
        login = st.text_input("Usuário",placeholder="seu login").strip().lower()
        senha = st.text_input("Senha",type="password")
        if st.button("Entrar",use_container_width=True,type="primary"):
            u2 = D["usuarios"].get(login)
            if u2 and u2["senha"]==senha:
                if u2["perfil"]=="Bloqueado": st.error("Você não tem acesso ao sistema.")
                else: st.session_state.usuario=login; st.rerun()
            else: st.error("Usuário ou senha incorretos")
        st.caption("Fale com a Alessandra para recuperar sua senha")
    st.stop()

u    = D["usuarios"][st.session_state.usuario]
perf = u["perfil"]

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚡ Power Financeiro")
    st.markdown(f"**{u['nome']}** · {perf}")
    st.markdown("---")
    menus=[]
    if pode(perf,"painel"):      menus.append("📊 Painel")
    if pode(perf,"lancar"):      menus.append("➕ Lançar")
    if pode(perf,"extrato"):     menus.append("📋 Extrato")
    if pode(perf,"orcamentos"):  menus.append("📄 Orçamentos")
    if pode(perf,"agenda"):      menus.append("📅 Agenda de Recebimentos")
    if pode(perf,"contas_pagar"):menus.append("💳 Contas a Pagar")
    if pode(perf,"relatorio"):   menus.append("📊 Relatório do Mês")
    if pode(perf,"config"):      menus.append("⚙️ Configurações")
    aba = st.radio("Menu",menus,label_visibility="collapsed")
    st.markdown("---")
    if st.button("Sair",use_container_width=True):
        st.session_state.usuario=None; st.rerun()

hoje = date.today()

# ══════════════════════════════════════════════════════════════════════════════
# PAINEL
# ══════════════════════════════════════════════════════════════════════════════
if aba=="📊 Painel":
    st.markdown(f"## 📊 Painel &nbsp;<span style='font-size:13px;color:#94a3b8;font-weight:400'>{hoje.strftime('%d/%m/%Y')}</span>",unsafe_allow_html=True)

    s_sic = saldo_conta("sicredi")
    s_ita = saldo_conta("itau")
    s_gil = saldo_conta("gilmar")
    a_rec = sum(o["valor"] for o in D["orcamentos"] if o.get("status_rec","Pendente")=="Pendente")
    n_rec = len([o for o in D["orcamentos"] if o.get("status_rec","Pendente")=="Pendente"])
    cp_ab = sum(c["valor"] for c in D.get("contas_pagar",[]) if c["status"] in ("Em aberto","Vencido"))

    # alertas vencimento próximo (7 dias)
    alertas=[]
    for cp in D.get("contas_pagar",[]):
        if cp["status"] in ("Em aberto","Vencido"):
            dv=parse_date(cp.get("vencimento",""))
            if dv:
                dias=(dv-hoje).days
                if dias<0: alertas.append(f"🔴 VENCIDO: {cp['beneficiario']} — {fmt(cp['valor'])} (venceu {cp['vencimento']})")
                elif dias<=7: alertas.append(f"🟡 Vence em {dias}d: {cp['beneficiario']} — {fmt(cp['valor'])} ({cp['vencimento']})")

    for a in alertas[:3]:
        bg="alert-red" if "VENCIDO" in a else "alert-amber"
        st.markdown(f'<div class="alert-box {bg}">{a}</div>',unsafe_allow_html=True)

    # cards
    c1,c2,c3,c4,c5 = st.columns(5)
    for col,label,val,cor,sub in [
        (c1,"Sicredi Power",s_sic,"green" if s_sic>=0 else "red","Conta principal"),
        (c2,"Deivid Itaú",s_ita,"green" if s_ita>=0 else "red","Despesas / pagamentos"),
        (c3,"A Receber",a_rec,"blue",f"{n_rec} orçamentos pendentes"),
        (c4,"Contas a Pagar",cp_ab,"red" if cp_ab>0 else "green","Boletos + despesas"),
        (c5,"Entradas (total)",sum(l["valor"] for l in D["lancamentos"] if l["tipo"]=="Entrada"),"green","Todos os lançamentos"),
    ]:
        with col:
            st.markdown(f'<div class="card"><div class="card-label">{label}</div><div class="card-value {cor}">{fmt(val)}</div><div class="card-sub">{sub}</div></div>',unsafe_allow_html=True)

    st.markdown("<br>",unsafe_allow_html=True)

    # resumo conta gilmar
    mes_a = hoje.strftime("%m/%Y")
    ge = sum(l["valor"] for l in D["lancamentos"] if l["tipo"]=="Entrada" and l["conta"]=="gilmar" and l["data"][3:]==mes_a)
    gs = sum(l["valor"] for l in D["lancamentos"] if l["tipo"]=="Saída" and l["conta"]=="gilmar" and l["data"][3:]==mes_a)
    st.markdown(f"""<div style="background:#f4ecf7;border:1px solid #d7bde2;border-radius:12px;padding:11px 18px;margin-bottom:16px;display:flex;align-items:center;gap:28px">
      <span style="font-size:12px;color:#6c3483;font-weight:700">📋 CONTA GILMAR — {mes_a}</span>
      <span style="font-size:12px;color:#64748b">Entrou: <b style="color:#0f6e56">{fmt(ge)}</b></span>
      <span style="font-size:12px;color:#64748b">Saiu: <b style="color:#c0392b">{fmt(gs)}</b></span>
      <span style="font-size:12px;color:#64748b">Saldo mês: <b style="color:#6c3483">{fmt(ge-gs)}</b></span>
    </div>""",unsafe_allow_html=True)

    col_a,col_b = st.columns([1.6,1])
    with col_a:
        st.markdown('<div class="section-title">🕐 Últimos lançamentos</div>',unsafe_allow_html=True)
        lancs=sorted(D["lancamentos"],key=lambda x:x["id"],reverse=True)[:12]
        if lancs:
            for l in lancs:
                tipo=l["tipo"]; ctag="entrada" if tipo=="Entrada" else "saida" if tipo=="Saída" else "transf"
                sinal="+" if tipo=="Entrada" else "↔" if tipo=="Transferência" else "-"
                cval="#0f6e56" if tipo=="Entrada" else "#185fa5" if tipo=="Transferência" else "#c0392b"
                cnome=D["contas"].get(l["conta"],{}).get("nome",l["conta"])
                st.markdown(f"""<div class="lanc-row">
                  <span class="tag tag-{ctag}">{tipo}</span>
                  <div style="flex:1;min-width:0">
                    <div style="font-size:13px;font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{l['beneficiario']}</div>
                    <div style="font-size:11px;color:#64748b">{l['data']} · {cnome} · {l['categoria']}</div>
                  </div>
                  <div style="font-weight:700;color:{cval};white-space:nowrap">{sinal} {fmt(l['valor'])}</div>
                </div>""",unsafe_allow_html=True)
        else: st.info("Nenhum lançamento ainda.")

    with col_b:
        st.markdown('<div class="section-title">📊 A Receber por cliente</div>',unsafe_allow_html=True)
        orcs_p=[o for o in D["orcamentos"] if o.get("status_rec","Pendente")=="Pendente"]
        if orcs_p:
            df_c=pd.DataFrame(orcs_p).groupby("cliente")["valor"].sum().reset_index().sort_values("valor",ascending=False).head(8)
            fig=px.bar(df_c,x="valor",y="cliente",orientation="h",color_discrete_sequence=["#185fa5"],labels={"valor":"R$","cliente":""})
            fig.update_layout(margin=dict(l=0,r=0,t=5,b=0),height=220,plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)")
            fig.update_xaxes(showgrid=True,gridcolor="#f0f0f0",tickformat=",.0f"); fig.update_yaxes(showgrid=False)
            st.plotly_chart(fig,use_container_width=True)

        # proximos vencimentos contas a pagar
        st.markdown('<div class="section-title">💳 Próximos vencimentos</div>',unsafe_allow_html=True)
        prox=[c for c in D.get("contas_pagar",[]) if c["status"] in ("Em aberto","Vencido")]
        prox=sorted(prox,key=lambda x: parse_date(x.get("vencimento","")) or date(2099,1,1))[:5]
        if prox:
            for cp in prox:
                dv=parse_date(cp.get("vencimento",""))
                dias=(dv-hoje).days if dv else 999
                cor="#c0392b" if dias<0 else "#ba7517" if dias<=7 else "#185fa5"
                txt="VENCIDO" if dias<0 else f"{dias}d" if dias<=30 else cp.get("vencimento","")
                st.markdown(f"""<div style="display:flex;justify-content:space-between;padding:7px 10px;border:1px solid #e2e8f0;border-radius:8px;margin-bottom:5px;align-items:center">
                  <div><div style="font-size:13px;font-weight:600">{cp['beneficiario']}</div>
                  <div style="font-size:11px;color:#64748b">{cp.get('categoria','—')}</div></div>
                  <div style="text-align:right"><div style="font-weight:700;color:#c0392b">{fmt(cp['valor'])}</div>
                  <div style="font-size:11px;color:{cor};font-weight:600">{txt}</div></div>
                </div>""",unsafe_allow_html=True)
        else: st.info("Nenhuma conta a pagar cadastrada")

# ══════════════════════════════════════════════════════════════════════════════
# LANÇAR
# ══════════════════════════════════════════════════════════════════════════════
elif aba=="➕ Lançar":
    st.markdown("## ➕ Novo Lançamento")
    tipo=st.radio("Tipo",["Entrada","Saída","Transferência"],horizontal=True)
    c1,c2=st.columns(2)
    with c1:
        data_l=st.date_input("Data",value=hoje)
        valor=st.number_input("Valor (R$)",min_value=0.01,step=0.01,format="%.2f")
        cd={k:D["contas"][k]["nome"] for k in D["contas"] if not (perf=="Operacional" and k=="gilmar")}
        conta=st.selectbox("Conta",options=list(cd.keys()),format_func=lambda x:cd[x])
        if tipo=="Transferência":
            dd={k:v for k,v in cd.items() if k!=conta}
            conta_dest=st.selectbox("Conta destino",options=list(dd.keys()),format_func=lambda x:dd[x])
        else: conta_dest=None
    with c2:
        categoria=st.selectbox("Categoria",D["categorias"])
        empresa=st.selectbox("Empresa",["Power Eletric","Power Equipamentos","Casa","Pessoal / Sócio","Geral"])
        beneficiario=st.text_input("Beneficiário / Origem")
        st.info(f"Lançado por: **{u['nome']}**")
    descricao=st.text_area("Descrição",height=70)
    if st.button("✅ Confirmar Lançamento",type="primary",use_container_width=True):
        if valor<=0: st.error("Informe um valor válido")
        elif not beneficiario: st.error("Informe o beneficiário")
        else:
            nid=max([l["id"] for l in D["lancamentos"]],default=0)+1
            D["lancamentos"].append({"id":nid,"data":data_l.strftime("%d/%m/%Y"),"tipo":tipo,
                "conta":conta,"conta_destino":conta_dest,"categoria":categoria,"empresa":empresa,
                "beneficiario":beneficiario,"descricao":descricao,"valor":float(valor),"lancado_por":u["nome"]})
            salvar(); st.success(f"✅ {fmt(valor)} lançado!"); st.rerun()
    if perf=="Admin":
        st.markdown("---")
        st.markdown("#### 🏦 Saldo inicial das contas")
        c1,c2,c3=st.columns(3)
        for cid,col in zip(["sicredi","itau","gilmar"],[c1,c2,c3]):
            with col:
                ns=st.number_input(D["contas"][cid]["nome"],value=float(D["contas"][cid]["saldo"]),step=0.01,format="%.2f",key=f"s_{cid}")
                if st.button("Salvar",key=f"b_{cid}"):
                    D["contas"][cid]["saldo"]=ns; salvar(); st.success("Salvo!")

# ══════════════════════════════════════════════════════════════════════════════
# EXTRATO
# ══════════════════════════════════════════════════════════════════════════════
elif aba=="📋 Extrato":
    st.markdown("## 📋 Extrato")
    c1,c2,c3=st.columns(3)
    fc=c1.selectbox("Conta",["Todas"]+[D["contas"][c]["nome"] for c in D["contas"]])
    ft=c2.selectbox("Tipo",["Todos","Entrada","Saída","Transferência"])
    fcat=c3.selectbox("Categoria",["Todas"]+D["categorias"])
    lancs=D["lancamentos"].copy()
    if fc!="Todas":
        cid=next(c for c in D["contas"] if D["contas"][c]["nome"]==fc)
        lancs=[l for l in lancs if l["conta"]==cid or l.get("conta_destino")==cid]
    if ft!="Todos": lancs=[l for l in lancs if l["tipo"]==ft]
    if fcat!="Todas": lancs=[l for l in lancs if l["categoria"]==fcat]
    lancs=sorted(lancs,key=lambda x:x["id"],reverse=True)
    te=sum(l["valor"] for l in lancs if l["tipo"]=="Entrada")
    ts=sum(l["valor"] for l in lancs if l["tipo"]=="Saída")
    c1,c2,c3=st.columns(3); c1.metric("Entradas",fmt(te)); c2.metric("Saídas",fmt(ts)); c3.metric("Saldo",fmt(te-ts))
    st.markdown("---")
    for l in lancs:
        tipo=l["tipo"]; sinal="+" if tipo=="Entrada" else "↔" if tipo=="Transferência" else "-"
        cnome=D["contas"].get(l["conta"],{}).get("nome",l["conta"])
        with st.expander(f"{l['data']}  |  {l['beneficiario']}  |  {sinal} {fmt(l['valor'])}"):
            c1,c2,c3=st.columns(3)
            c1.write(f"**Tipo:** {tipo}"); c1.write(f"**Categoria:** {l['categoria']}")
            c2.write(f"**Conta:** {cnome}"); c2.write(f"**Empresa:** {l.get('empresa','—')}")
            c3.write(f"**Lançado por:** {l.get('lancado_por','—')}"); c3.write(f"**Descrição:** {l.get('descricao','—')}")
            if perf=="Admin":
                if st.button("🗑️ Excluir",key=f"del_{l['id']}"):
                    D["lancamentos"]=[x for x in D["lancamentos"] if x["id"]!=l["id"]]; salvar(); st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# ORÇAMENTOS
# ══════════════════════════════════════════════════════════════════════════════
elif aba=="📄 Orçamentos":
    st.markdown("## 📄 Orçamentos e Notas a Receber")
    tab1,tab2,tab3=st.tabs(["📋 Lista","➕ Novo RDO / Orçamento","✏️ Completar (NF / Recebimento)"])
    with tab1:
        c1,c2,c3=st.columns(3)
        fcli=c1.selectbox("Cliente",["Todos"]+sorted(set(o["cliente"] for o in D["orcamentos"])))
        fresp=c2.selectbox("Responsável",["Todos"]+sorted(set(o["responsavel"] for o in D["orcamentos"])))
        fst=c3.selectbox("Status",["Todos","Pendente","Recebido"])
        orcs=D["orcamentos"].copy()
        if fcli!="Todos": orcs=[o for o in orcs if o["cliente"]==fcli]
        if fresp!="Todos": orcs=[o for o in orcs if o["responsavel"]==fresp]
        if fst!="Todos": orcs=[o for o in orcs if o.get("status_rec","Pendente")==fst]
        tp=sum(o["valor"] for o in orcs if o.get("status_rec","Pendente")=="Pendente")
        tr=sum(o["valor"] for o in orcs if o.get("status_rec","")=="Recebido")
        c1,c2,c3=st.columns(3); c1.metric("Listados",len(orcs)); c2.metric("Pendente",fmt(tp)); c3.metric("Recebido",fmt(tr))
        st.markdown("---")
        for o in orcs:
            st_rec=o.get("status_rec","Pendente"); icon="🟡" if st_rec=="Pendente" else "✅"
            with st.expander(f"{icon} Orç.{o['num']} | {o['cliente']} | {fmt(o['valor'])} | {o['responsavel']}"):
                c1,c2=st.columns(2)
                c1.write(f"**Serviço:** {o['servico']}"); c1.write(f"**NF:** {o.get('n_nf','—')}")
                c2.write(f"**Previsão:** {o.get('prev_rec','—')}"); c2.write(f"**PC:** {o.get('n_ped','—')}"); c2.write(f"**Obs:** {o.get('obs','—')}")
    with tab2:
        st.markdown("#### Novo RDO / Orçamento")
        c1,c2=st.columns(2)
        with c1:
            nn=st.text_input("Número"); nc=st.text_input("Cliente"); nr=st.text_input("Responsável / Supervisor")
            ns_=st.text_area("Descrição do serviço",height=70); ncolab=st.text_area("Colaboradores",height=50)
        with c2:
            nv=st.number_input("Valor (R$)",min_value=0.0,step=0.01,format="%.2f")
            ndt=st.date_input("Data do serviço",value=hoje)
            nemp=st.selectbox("Empresa",["Power Eletric","Power Equipamentos"])
            nobs=st.text_area("Observações",height=50)
        if st.button("✅ Cadastrar",type="primary"):
            if not nc or not ns_: st.error("Preencha cliente e serviço")
            else:
                nid=max([o["id"] for o in D["orcamentos"]],default=0)+1
                D["orcamentos"].append({"id":nid,"num":nn,"cliente":nc,"responsavel":nr,"servico":ns_,
                    "colaboradores":ncolab,"valor":float(nv),"data_serv":ndt.strftime("%d/%m/%Y"),
                    "empresa":nemp,"prev_rec":"","n_nf":"","n_ped":"","status_rec":"Pendente",
                    "obs":nobs,"lancado_por":u["nome"]})
                salvar(); st.success("Cadastrado!"); st.rerun()
    with tab3:
        if not pode(perf,"completar_orc"): st.warning("Apenas Elisangela, Alessandra ou Gilmar podem completar.")
        else:
            st.markdown("#### Completar — NF, Pedido de Compra, Recebimento")
            pend=[o for o in D["orcamentos"] if not o.get("n_nf") or o.get("status_rec","Pendente")=="Pendente"]
            if not pend: st.success("Todos os orçamentos estão completos!")
            for o in pend:
                with st.expander(f"Orç.{o['num']} | {o['cliente']} | {fmt(o['valor'])}"):
                    c1,c2,c3=st.columns(3)
                    nnf2=c1.text_input("Nota Fiscal",value=o.get("n_nf",""),key=f"nf_{o['id']}")
                    nped2=c2.text_input("Pedido Compra",value=o.get("n_ped",""),key=f"ped_{o['id']}")
                    nprev=c3.text_input("Previsão recebimento",value=o.get("prev_rec",""),key=f"prev_{o['id']}")
                    nst2=st.selectbox("Status",["Pendente","Recebido"],index=0 if o.get("status_rec","Pendente")=="Pendente" else 1,key=f"st2_{o['id']}")
                    nobs2=st.text_input("Obs",value=o.get("obs",""),key=f"ob2_{o['id']}")
                    if st.button("💾 Salvar",key=f"sv2_{o['id']}"):
                        for oo in D["orcamentos"]:
                            if oo["id"]==o["id"]:
                                oo["n_nf"]=nnf2; oo["n_ped"]=nped2; oo["prev_rec"]=nprev
                                oo["status_rec"]=nst2; oo["obs"]=nobs2
                                if nst2=="Recebido": oo["dt_recebimento"]=hoje.strftime("%d/%m/%Y")
                        salvar(); st.success("Salvo!"); st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# AGENDA DE RECEBIMENTOS
# ══════════════════════════════════════════════════════════════════════════════
elif aba=="📅 Agenda de Recebimentos":
    st.markdown("## 📅 Agenda de Recebimentos")

    # filtro período
    col1,col2=st.columns(2)
    periodo=col1.selectbox("Período",["Esta semana","Este mês","Próximo mês","Próximos 3 meses","Sem data definida","Todos pendentes"])
    fcli2=col2.selectbox("Cliente",["Todos"]+sorted(set(o["cliente"] for o in D["orcamentos"])))

    orcs_p=[o for o in D["orcamentos"] if o.get("status_rec","Pendente")=="Pendente"]
    if fcli2!="Todos": orcs_p=[o for o in orcs_p if o["cliente"]==fcli2]

    def filtrar_periodo(orcs,periodo):
        ini=hoje; fim=hoje
        if periodo=="Esta semana":
            ini=hoje-timedelta(days=hoje.weekday()); fim=ini+timedelta(days=6)
        elif periodo=="Este mês":
            ini=hoje.replace(day=1); fim=(ini.replace(month=ini.month%12+1,day=1) if ini.month<12 else ini.replace(year=ini.year+1,month=1,day=1))-timedelta(days=1)
        elif periodo=="Próximo mês":
            ini=(hoje.replace(day=1).replace(month=hoje.month%12+1) if hoje.month<12 else hoje.replace(year=hoje.year+1,month=1,day=1))
            fim=(ini.replace(month=ini.month%12+1,day=1) if ini.month<12 else ini.replace(year=ini.year+1,month=1,day=1))-timedelta(days=1)
        elif periodo=="Próximos 3 meses":
            fim=hoje+timedelta(days=90)
        elif periodo=="Sem data definida":
            return [o for o in orcs if not o.get("prev_rec")]
        elif periodo=="Todos pendentes":
            return orcs

        resultado=[]
        for o in orcs:
            d=parse_date(o.get("prev_rec",""))
            if d and ini<=d<=fim: resultado.append(o)
        return resultado

    filtrados=filtrar_periodo(orcs_p,periodo)
    total_f=sum(o["valor"] for o in filtrados)

    c1,c2,c3=st.columns(3)
    c1.metric("Orçamentos",len(filtrados))
    c2.metric("Total a receber",fmt(total_f))
    c3.metric("Sem data definida",len([o for o in orcs_p if not o.get("prev_rec")]))
    st.markdown("---")

    if not filtrados:
        st.info(f"Nenhum orçamento pendente para o período: **{periodo}**")
    else:
        # agrupa por cliente
        df_ag=pd.DataFrame(filtrados)
        for cli in sorted(df_ag["cliente"].unique()):
            cli_orcs=[o for o in filtrados if o["cliente"]==cli]
            total_cli=sum(o["valor"] for o in cli_orcs)
            st.markdown(f"### 🏢 {cli} &nbsp;<span style='font-size:14px;color:#185fa5'>{fmt(total_cli)}</span>",unsafe_allow_html=True)
            for o in cli_orcs:
                dv=parse_date(o.get("prev_rec",""))
                dias=(dv-hoje).days if dv else None
                if dias is not None:
                    cor="#c0392b" if dias<0 else "#ba7517" if dias<=7 else "#0f6e56"
                    prazo=f"<span style='color:{cor};font-weight:600'>{'ATRASADO' if dias<0 else f'em {dias}d'}</span>"
                else: prazo="<span style='color:#94a3b8'>sem data</span>"
                st.markdown(f"""<div class="lanc-row">
                  <span class="tag tag-pendente">Pendente</span>
                  <div style="flex:1;min-width:0">
                    <div style="font-size:13px;font-weight:600">Orç.{o['num']} — {o['servico'][:60]}</div>
                    <div style="font-size:11px;color:#64748b">Resp: {o['responsavel']} · NF: {o.get('n_nf','—')} · Prev: {o.get('prev_rec','—')} · {prazo}</div>
                  </div>
                  <div style="font-weight:700;color:#185fa5;white-space:nowrap">{fmt(o['valor'])}</div>
                </div>""",unsafe_allow_html=True)
            st.markdown("<br>",unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# CONTAS A PAGAR
# ══════════════════════════════════════════════════════════════════════════════
elif aba=="💳 Contas a Pagar":
    st.markdown("## 💳 Contas a Pagar")
    tab1,tab2=st.tabs(["📋 Em aberto / Pagas","➕ Nova conta a pagar"])

    with tab1:
        c1,c2,c3=st.columns(3)
        fst2=c1.selectbox("Status",["Todas","Em aberto","Vencido","Pago"])
        fcat2=c2.selectbox("Categoria",["Todas"]+D["categorias"])
        femp2=c3.selectbox("Empresa",["Todas","Power Eletric","Power Equipamentos","Casa","Pessoal / Sócio","Geral"])

        contas_p=D.get("contas_pagar",[])
        # atualiza vencidas
        for cp in contas_p:
            if cp["status"]=="Em aberto":
                dv=parse_date(cp.get("vencimento",""))
                if dv and dv<hoje: cp["status"]="Vencido"

        lista=contas_p.copy()
        if fst2!="Todas": lista=[c for c in lista if c["status"]==fst2]
        if fcat2!="Todas": lista=[c for c in lista if c.get("categoria","")==fcat2]
        if femp2!="Todas": lista=[c for c in lista if c.get("empresa","")==femp2]
        lista=sorted(lista,key=lambda x:(0 if x["status"]=="Vencido" else 1 if x["status"]=="Em aberto" else 2))

        tab_ab=sum(c["valor"] for c in contas_p if c["status"] in ("Em aberto","Vencido"))
        tab_vc=sum(c["valor"] for c in contas_p if c["status"]=="Vencido")
        tab_pg=sum(c["valor"] for c in contas_p if c["status"]=="Pago")
        c1,c2,c3=st.columns(3)
        c1.metric("Em aberto",fmt(tab_ab))
        c2.metric("Vencido",fmt(tab_vc))
        c3.metric("Pago",fmt(tab_pg))
        st.markdown("---")

        if not lista: st.info("Nenhuma conta encontrada.")
        for cp in lista:
            st_cp=cp["status"]
            icon="🔴" if st_cp=="Vencido" else "🟡" if st_cp=="Em aberto" else "✅"
            dv=parse_date(cp.get("vencimento",""))
            dias=(dv-hoje).days if dv else None
            prazo_txt=f" · {'VENCIDO há '+str(abs(dias))+'d' if dias is not None and dias<0 else str(dias)+'d para vencer' if dias is not None else ''}"
            with st.expander(f"{icon} {cp['beneficiario']} | {fmt(cp['valor'])} | {cp.get('vencimento','—')}{prazo_txt}"):
                c1,c2=st.columns(2)
                c1.write(f"**Categoria:** {cp.get('categoria','—')}")
                c1.write(f"**Empresa:** {cp.get('empresa','—')}")
                c1.write(f"**Descrição:** {cp.get('descricao','—')}")
                c2.write(f"**Vencimento:** {cp.get('vencimento','—')}")
                c2.write(f"**Lançado por:** {cp.get('lancado_por','—')}")
                c2.write(f"**Obs:** {cp.get('obs','—')}")
                if st_cp=="Pago":
                    st.success(f"✅ Pago em {cp.get('data_pagamento','—')} · Conta: {D['contas'].get(cp.get('conta_pagamento',''),{}).get('nome','—')} · {fmt(cp.get('valor_pago'))}")

                if st_cp in ("Em aberto","Vencido") and pode(perf,"lancar"):
                    st.markdown("**Registrar pagamento:**")
                    pc1,pc2,pc3=st.columns(3)
                    cp_conta=pc1.selectbox("Conta que pagou",options=list(D["contas"].keys()),format_func=lambda x:D["contas"][x]["nome"],key=f"cpc_{cp['id']}")
                    cp_data=pc2.date_input("Data pagamento",value=hoje,key=f"cpd_{cp['id']}")
                    cp_valpag=pc3.number_input("Valor pago",min_value=0.01,value=float(cp["valor"]),step=0.01,format="%.2f",key=f"cpv_{cp['id']}")
                    if st.button("✅ Marcar como pago",key=f"cpb_{cp['id']}",type="primary"):
                        for ccp in D["contas_pagar"]:
                            if ccp["id"]==cp["id"]:
                                ccp["status"]="Pago"; ccp["conta_pagamento"]=cp_conta
                                ccp["data_pagamento"]=cp_data.strftime("%d/%m/%Y"); ccp["valor_pago"]=float(cp_valpag)
                        nid=max([l["id"] for l in D["lancamentos"]],default=0)+1
                        D["lancamentos"].append({"id":nid,"data":cp_data.strftime("%d/%m/%Y"),"tipo":"Saída",
                            "conta":cp_conta,"conta_destino":None,"categoria":cp.get("categoria","Boleto / Fornecedor"),
                            "empresa":cp.get("empresa","Geral"),"beneficiario":cp["beneficiario"],
                            "descricao":f"Pgto: {cp.get('descricao','')}","valor":float(cp_valpag),"lancado_por":u["nome"]})
                        salvar(); st.success("✅ Pago! Lançado automaticamente no extrato!"); st.rerun()

                if perf=="Admin":
                    if st.button("🗑️ Excluir",key=f"cpd2_{cp['id']}"):
                        D["contas_pagar"]=[x for x in D["contas_pagar"] if x["id"]!=cp["id"]]; salvar(); st.rerun()

    with tab2:
        st.markdown("#### Nova conta a pagar")
        c1,c2=st.columns(2)
        with c1:
            cpb=st.text_input("Beneficiário / Fornecedor")
            cpv=st.number_input("Valor (R$)",min_value=0.01,step=0.01,format="%.2f")
            cpvc=st.date_input("Vencimento")
            cpcat=st.selectbox("Categoria",D["categorias"])
        with c2:
            cpemp=st.selectbox("Empresa",["Power Eletric","Power Equipamentos","Casa","Pessoal / Sócio","Geral"])
            cpd=st.text_area("Descrição",height=70)
            cpo=st.text_input("Observação")
        if st.button("✅ Cadastrar conta a pagar",type="primary",use_container_width=True):
            if not cpb or cpv<=0: st.error("Preencha beneficiário e valor")
            else:
                if "contas_pagar" not in D: D["contas_pagar"]=[]
                nid=max([c["id"] for c in D["contas_pagar"]],default=0)+1
                D["contas_pagar"].append({"id":nid,"beneficiario":cpb,"valor":float(cpv),
                    "vencimento":cpvc.strftime("%d/%m/%Y"),"categoria":cpcat,"empresa":cpemp,
                    "descricao":cpd,"obs":cpo,"status":"Em aberto","lancado_por":u["nome"],
                    "conta_pagamento":None,"data_pagamento":None,"valor_pago":None})
                salvar(); st.success("Cadastrado!"); st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# RELATÓRIO DO MÊS
# ══════════════════════════════════════════════════════════════════════════════
elif aba=="📊 Relatório do Mês":
    st.markdown("## 📊 Relatório do Mês")

    # seletor mês
    meses=sorted(set(l["data"][3:] for l in D["lancamentos"]),reverse=True)
    if not meses: st.info("Nenhum lançamento ainda."); st.stop()
    mes_sel=st.selectbox("Selecione o mês",meses)
    mm,aa=mes_sel.split("/")

    lancs_mes=[l for l in D["lancamentos"] if l["data"][3:]==mes_sel]
    te=sum(l["valor"] for l in lancs_mes if l["tipo"]=="Entrada")
    ts=sum(l["valor"] for l in lancs_mes if l["tipo"]=="Saída")
    tt=sum(l["valor"] for l in lancs_mes if l["tipo"]=="Transferência")

    c1,c2,c3,c4=st.columns(4)
    c1.metric("Entradas",fmt(te))
    c2.metric("Saídas",fmt(ts))
    c3.metric("Transferências",fmt(tt))
    c4.metric("Saldo do mês",fmt(te-ts),delta=f"R$ {te-ts:,.0f}".replace(",","."))
    st.markdown("---")

    col_a,col_b=st.columns(2)
    with col_a:
        st.markdown("#### Saídas por categoria")
        df_s=pd.DataFrame([l for l in lancs_mes if l["tipo"]=="Saída"])
        if not df_s.empty:
            df_sg=df_s.groupby("categoria")["valor"].sum().reset_index().sort_values("valor",ascending=False)
            fig=px.bar(df_sg,x="categoria",y="valor",color_discrete_sequence=["#c0392b"],labels={"valor":"R$","categoria":""})
            fig.update_layout(margin=dict(l=0,r=0,t=5,b=0),height=300,plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)")
            fig.update_xaxes(tickangle=45); st.plotly_chart(fig,use_container_width=True)
            st.dataframe(df_sg.rename(columns={"categoria":"Categoria","valor":"Valor (R$)"}),use_container_width=True,hide_index=True)
        else: st.info("Nenhuma saída neste mês")

    with col_b:
        st.markdown("#### Entradas por categoria")
        df_e=pd.DataFrame([l for l in lancs_mes if l["tipo"]=="Entrada"])
        if not df_e.empty:
            df_eg=df_e.groupby("categoria")["valor"].sum().reset_index().sort_values("valor",ascending=False)
            fig2=px.bar(df_eg,x="categoria",y="valor",color_discrete_sequence=["#0f6e56"],labels={"valor":"R$","categoria":""})
            fig2.update_layout(margin=dict(l=0,r=0,t=5,b=0),height=300,plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)")
            fig2.update_xaxes(tickangle=45); st.plotly_chart(fig2,use_container_width=True)
            st.dataframe(df_eg.rename(columns={"categoria":"Categoria","valor":"Valor (R$)"}),use_container_width=True,hide_index=True)
        else: st.info("Nenhuma entrada neste mês")

    st.markdown("---")
    st.markdown("#### Saídas por empresa")
    df_emp=pd.DataFrame([l for l in lancs_mes if l["tipo"]=="Saída"])
    if not df_emp.empty and "empresa" in df_emp.columns:
        df_empg=df_emp.groupby("empresa")["valor"].sum().reset_index().sort_values("valor",ascending=False)
        fig3=px.pie(df_empg,values="valor",names="empresa",hole=0.4,color_discrete_sequence=px.colors.sequential.Blues_r)
        fig3.update_layout(margin=dict(l=0,r=0,t=10,b=0),height=280,paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig3,use_container_width=True)

    st.markdown("#### Todos os lançamentos do mês")
    df_show=pd.DataFrame(lancs_mes)[["data","tipo","beneficiario","categoria","valor","lancado_por"]] if lancs_mes else pd.DataFrame()
    if not df_show.empty:
        df_show["valor"]=df_show["valor"].apply(lambda x: f"R$ {x:,.2f}".replace(",","X").replace(".",",").replace("X","."))
        df_show.columns=["Data","Tipo","Beneficiário","Categoria","Valor","Lançado por"]
        st.dataframe(df_show,use_container_width=True,hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÕES
# ══════════════════════════════════════════════════════════════════════════════
elif aba=="⚙️ Configurações":
    st.markdown("## ⚙️ Configurações")
    tab1,tab2,tab3=st.tabs(["👥 Usuários","🏷️ Categorias","🏦 Contas"])
    with tab1:
        perfis_op=["Admin","Socio","Operacional","RDO","Bloqueado"]
        for uid,uu in D["usuarios"].items():
            with st.expander(f"{uu['nome']} · {uu['perfil']}"):
                c1,c2,c3=st.columns(3)
                nn2=c1.text_input("Nome",value=uu["nome"],key=f"un_{uid}")
                np2=c2.selectbox("Perfil",perfis_op,index=perfis_op.index(uu["perfil"]) if uu["perfil"] in perfis_op else 0,key=f"up_{uid}")
                ns2=c3.text_input("Nova senha",type="password",placeholder="vazio = não altera",key=f"us_{uid}")
                if st.button("Salvar",key=f"ub_{uid}"):
                    D["usuarios"][uid]["nome"]=nn2; D["usuarios"][uid]["perfil"]=np2
                    if ns2: D["usuarios"][uid]["senha"]=ns2
                    salvar(); st.success("Salvo!")
    with tab2:
        st.caption("Adicione ou remova categorias")
        for i,c in enumerate(D["categorias"]):
            c1,c2=st.columns([5,1]); c1.write(f"• {c}")
            if c2.button("🗑️",key=f"dc_{i}"):
                D["categorias"].pop(i); salvar(); st.rerun()
        st.markdown("---")
        ncat=st.text_input("Nova categoria")
        if st.button("➕ Adicionar",type="primary"):
            if ncat and ncat not in D["categorias"]:
                D["categorias"].append(ncat); salvar(); st.success(f"'{ncat}' adicionada!"); st.rerun()
            elif ncat: st.warning("Já existe!")
    with tab3:
        for cid in D["contas"]:
            cc=D["contas"][cid]
            with st.expander(cc["nome"]):
                nn3=st.text_input("Nome",value=cc["nome"],key=f"cn_{cid}")
                if st.button("Salvar",key=f"cb_{cid}"):
                    D["contas"][cid]["nome"]=nn3; salvar(); st.success("Salvo!")
