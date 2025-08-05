import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Define a configuração da página para um layout mais amplo e título
st.set_page_config(layout="wide", page_title="Dashboard de Plano de Ação", page_icon="📝")

# Função para carregar os dados do Excel
# Usamos st.cache_data para evitar recarregar o arquivo toda vez que o app for atualizado
@st.cache_data
def load_data(file_path):
    try:
        # Tenta ler o arquivo Excel
        df = pd.read_excel(file_path, engine='openpyxl')
        
        # --- MUDANÇA CRÍTICA AQUI: NORMALIZAÇÃO ROBUSTA DOS NOMES DAS COLUNAS ---
        # Converte para minúsculas e substitui qualquer caractere que NÃO seja a-z ou 0-9 por um underscore
        # Isso tratará espaços, parênteses, barras, acentos, etc.
        df.columns = df.columns.str.lower().str.replace('[^a-z0-9]', '_', regex=True)
        # Remove múltiplos underscores consecutivos (ex: '__' vira '_')
        df.columns = df.columns.str.replace(r'_{2,}', '_', regex=True)
        # Remove underscores no início ou no fim da string
        df.columns = df.columns.str.strip('_')
        # --- FIM DA MUDANÇA CRÍTICA ---

        # REMOVA A LINHA DE DEPURACAO AQUI: st.write("Colunas Normalizadas:", df.columns.tolist()) 

        # Verifica e converte a coluna 'data' para o formato de data/hora
        if 'data' in df.columns:
            df['data'] = pd.to_datetime(df['data'], errors='coerce') # 'coerce' transforma erros em NaT (Not a Time)
            # Remove linhas com 'data' inválida (NaT), se houver
            df.dropna(subset=['data'], inplace=True)
        else:
            st.warning("A coluna 'data' não foi encontrada na sua planilha. A funcionalidade de filtros por data e ações do dia pode não funcionar.")
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo Excel: {e}. Verifique se o arquivo está no formato correto e não está corrompido.")
        return pd.DataFrame() # Retorna um DataFrame vazio em caso de erro

# --- Título e Upload do Arquivo ---
st.title('📝 Dashboard Interativo de Plano de Ação')
st.write('Carregue sua planilha Excel para visualizar e gerenciar seu plano diário de atividades e objetivos.')

uploaded_file = st.file_uploader("👉 Escolha sua planilha Excel (.xlsx)", type="xlsx")

if uploaded_file:
    df = load_data(uploaded_file)

    if not df.empty:
        st.success("Planilha carregada com sucesso! 🎉")

        # --- Exibir os dados brutos carregados (OPCIONAL: PODE REMOVER DEPOIS DE TESTAR) ---
        # st.subheader('📋 Dados Carregados')
        # st.dataframe(df, use_container_width=True) 
        # st.markdown("---") # Separador visual
        # --- FIM OPCIONAL ---


        # --- Barra Lateral para Filtros ---
        st.sidebar.header('⚙️ Filtros')

        # Filtro por Dia da Semana
        if 'dia_da_semana' in df.columns:
            all_days = df['dia_da_semana'].unique().tolist()
            selected_days = st.sidebar.multiselect(
                'Dia da Semana', 
                options=all_days, 
                default=all_days # Seleciona todos por padrão
            )
            if selected_days:
                df_filtered = df[df['dia_da_semana'].isin(selected_days)]
            else:
                df_filtered = df # Se nenhum dia for selecionado, mostra tudo
        else:
            st.sidebar.warning("Coluna 'dia_da_semana' não encontrada para filtro.")
            df_filtered = df # Usa o DataFrame original se a coluna não existir

        # Filtro por Foco Principal (busca por palavra-chave)
        if 'foco_principal_do_dia' in df.columns:
            search_focus = st.sidebar.text_input('Buscar por Foco Principal (palavra-chave)')
            if search_focus:
                # Filtra linhas onde 'foco_principal_do_dia' contém a palavra-chave (case-insensitive)
                df_filtered = df_filtered[df_filtered['foco_principal_do_dia'].astype(str).str.contains(search_focus, case=False, na=False)]
        else:
            st.sidebar.info("Coluna 'foco_principal_do_dia' não encontrada para filtro de palavra-chave.")
        
        # --- Métricas e Resumo do Plano ---
        st.subheader('🔍 Resumo do Plano de Ação')
        col1, col2, col3 = st.columns(3)

        total_registros = len(df_filtered)
        col1.metric(label="Total de Registros (dias)", value=total_registros)

        if 'dia_da_semana' in df_filtered.columns:
            frequencia_dias = df_filtered['dia_da_semana'].value_counts()
            col2.metric(label="Dia com mais Registros", value=frequencia_dias.index[0] if not frequencia_dias.empty else "N/A")
        else:
            col2.info("Não foi possível determinar o dia com mais registros sem a coluna 'dia_da_semana'.")
        
        if 'foco_principal_do_dia' in df_filtered.columns:
            col3.metric(label="Focos Principais Distintos", value=df_filtered['foco_principal_do_dia'].nunique())
        else:
            col3.info("Não foi possível contar focos principais distintos sem a coluna 'foco_principal_do_dia'.")

        st.markdown("---") # Separador visual

        # --- Ações para o Dia Corrente (AGORA COM VISUALIZAÇÃO MELHORADA E NOMES CORRIGIDOS) ---
        st.subheader('🗓️ Ações e Metas para Hoje')
        hoje = datetime.today().date() # Pega a data atual sem a hora
        
        if 'data' in df_filtered.columns:
            # Filtra os registros cuja data é igual à data de hoje
            acoes_hoje = df_filtered[df_filtered['data'].dt.date == hoje]
            if not acoes_hoje.empty:
                st.warning('🚨 Você tem as seguintes ações/metas para hoje:')
                for index, row in acoes_hoje.iterrows():
                    st.markdown(f"**Dia:** {row.get('dia', 'N/A')} - **Dia da Semana:** {row.get('dia_da_semana', 'N/A')}")
                    st.markdown(f"**Foco Principal do Dia:** {row.get('foco_principal_do_dia', 'N/A')}")
                    
                    # --- REFERÊNCIA DE COLUNA 'atividades_essenciais_rotina_di_ria' CORRIGIDA ---
                    if 'atividades_essenciais_rotina_di_ria' in row and pd.notna(row['atividades_essenciais_rotina_di_ria']):
                        st.markdown(f"**Atividades Essenciais:**\n{row['atividades_essenciais_rotina_di_ria']}")
                    else:
                        st.markdown("Atividades Essenciais: Não informado.")

                    if 'notas_objetivos' in row and pd.notna(row['notas_objetivos']):
                        st.markdown(f"**Notas/Objetivos:**\n{row['notas_objetivos']}")
                    else:
                        st.markdown("Notas/Objetivos: Não informado.")
                    # --- FIM DAS REFERÊNCIAS DE COLUNAS CORRIGIDAS ---
                    st.markdown("---") # Separador para cada ação do dia
            else:
                st.info('✨ Nenhuma ação ou meta prevista para hoje. Aproveite o dia!')
        else:
            st.info('Para ver ações do dia corrente, sua planilha precisa de uma coluna "data".')

        st.markdown("---") # Separador visual

        # --- Detalhes Diários do Plano (NOVA SEÇÃO PARA VISUALIZAÇÃO COMPLETA) ---
        st.subheader('📖 Detalhes Diários do Plano de Ação')
        if not df_filtered.empty:
            st.info("Expanda cada dia para ver o foco, atividades e notas completas.")
            # Ordena por data para uma visualização cronológica
            df_display = df_filtered.sort_values(by='data', ascending=True)

            for index, row in df_display.iterrows():
                # Formata a data para exibir no título do expander
                display_date = row['data'].strftime('%d/%m/%Y') if pd.notna(row['data']) else 'Data Não Informada'
                expander_title = f"{display_date} - {row.get('dia_da_semana', 'N/A')} - {row.get('foco_principal_do_dia', 'N/A')}"
                
                with st.expander(expander_title):
                    st.markdown(f"**Dia (na planilha):** {row.get('dia', 'N/A')}")
                    st.markdown(f"**Foco Principal do Dia:** {row.get('foco_principal_do_dia', 'N/A')}")
                    
                    # --- REFERÊNCIA DE COLUNA 'atividades_essenciais_rotina_di_ria' CORRIGIDA ---
                    if 'atividades_essenciais_rotina_di_ria' in row and pd.notna(row['atividades_essenciais_rotina_di_ria']):
                        st.markdown(f"**Atividades Essenciais:**\n{row['atividades_essenciais_rotina_di_ria']}")
                    else:
                        st.markdown("Atividades Essenciais: Não informado.")

                    if 'notas_objetivos' in row and pd.notna(row['notas_objetivos']):
                        st.markdown(f"**Notas/Objetivos:**\n{row['notas_objetivos']}")
                    else:
                        st.markdown("Notas/Objetivos: Não informado.")
                    # --- FIM DAS REFERÊNCIAS DE COLUNAS CORRIGIDAS ---
        else:
            st.info("Nenhum registro encontrado com os filtros aplicados para exibir detalhes.")
        
        st.markdown("---") # Separador visual

        # --- Gráficos Interativos ---
        st.subheader('📊 Análise Gráfica')

        # Gráfico: Frequência de Foco Principal
        if 'foco_principal_do_dia' in df_filtered.columns and not df_filtered.empty:
            st.write("#### Frequência dos Focos Principais")
            focus_counts = df_filtered['foco_principal_do_dia'].value_counts().reset_index()
            focus_counts.columns = ['Foco Principal', 'Contagem']
            fig_focus = px.bar(
                focus_counts.head(10), # Exibe os 10 focos principais mais frequentes
                x='Foco Principal',
                y='Contagem',
                title='Top 10 Focos Principais',
                labels={'Foco Principal': 'Foco Principal do Dia', 'Contagem': 'Número de Ocorrências'}
            )
            fig_focus.update_xaxes(tickangle=45) # Inclina os rótulos do eixo X para melhor legibilidade
            st.plotly_chart(fig_focus, use_container_width=True)
        else:
            st.info("Coluna 'foco_principal_do_dia' não encontrada ou dados insuficientes para o gráfico de focos.")

        # Gráfico: Distribuição de Registros por Dia da Semana
        if 'dia_da_semana' in df_filtered.columns and not df_filtered.empty:
            st.write("#### Distribuição de Registros por Dia da Semana")
            # Define a ordem dos dias da semana para o gráfico
            day_order = ["Domingo", "Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado"]
            day_counts = df_filtered['dia_da_semana'].value_counts().reindex(day_order).fillna(0).reset_index()
            day_counts.columns = ['Dia da Semana', 'Contagem']
            fig_days = px.bar(
                day_counts,
                x='Dia da Semana',
                y='Contagem',
                title='Número de Registros por Dia da Semana',
                labels={'Dia da Semana': 'Dia da Semana', 'Contagem': 'Número de Registros'}
            )
            st.plotly_chart(fig_days, use_container_width=True)
        else:
            st.info("Coluna 'dia_da_semana' não encontrada ou dados insuficientes para o gráfico de distribuição por dia da semana.")

    else:
        st.warning("Nenhum dado foi carregado do arquivo Excel. Verifique o formato e o conteúdo da sua planilha.")
else:
    st.info('Aguardando o upload do seu arquivo Excel para iniciar o dashboard. Por favor, carregue sua planilha para continuar.')

# NOTA IMPORTANTE AO USUÁRIO SOBRE A COLUNA 'STATUS'
st.sidebar.markdown("---")
st.sidebar.markdown(
    "**💡 Sugestão para o futuro:** Sua planilha atual não contém uma coluna 'Status' "
    "(ex: 'Concluída', 'Em Andamento', 'Não Iniciada'). "
    "Para habilitar métricas detalhadas e filtros específicos por status de meta "
    "(como 'metas alcançadas', 'em andamento', etc.), "
    "por favor, considere adicionar esta coluna à sua planilha e preenchê-la com os status de cada item. "
    "Com essa coluna, o aplicativo poderia ser expandido para fornecer análises de progresso ainda mais precisas!"
)