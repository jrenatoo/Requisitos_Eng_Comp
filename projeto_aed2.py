#Análise dos pré-requisitos de Engenharia de Computação.

from pathlib import Path
import pandas as pd #responsavel pela tabela CSV e criação das tabelas de resultados.
import networkx as nx #criação do grafo.
import matplotlib.pyplot as plt #criação dos gráficos.


pasta = Path(__file__).parent
saida = pasta / 'resultados'
#Imagens produzidas ficarão dentro de "resultados".
saida.mkdir(exist_ok=True) #cria a pasta caso nao exista

# Leitura de dados e criação de grafos
disciplinas = pd.read_csv(pasta / 'disciplinas_grade.csv') #todas as disciplinas
arestas = pd.read_csv(pasta / 'arestas_prerequisitos.csv') #relações de pré-requisitos

grafo = nx.DiGraph() # Utilizado DiGraph pois as arestas têm sentido. Não foi necessário uso de pesos


for _, d in disciplinas.iterrows(): #percorre as linhas da tabela de disciplinas.
    grafo.add_node(d['codigo'], nome=d['disciplina'], nivel=int(d['nivel']))
    #Cada linha das disciplinas vira um nó. Disciplina e nivel sao os atributos.
for _, a in arestas.iterrows():
    grafo.add_edge(a['origem_codigo'], a['destino_codigo'])
    #Cada linha das relações vira uma aresta orientada.



#Calculo dos dependentes 
# Grau de saída = dependentes diretos.
# Descendentes = dependentes diretos e indiretos (alcançáveis no grafo).
ranking = [] 
for codigo in grafo.nodes:  #Para cada uma das matérias é verificado
    diretos = grafo.out_degree(codigo) #quantas setas saem do nó.
    total = len(nx.descendants(grafo, codigo)) #retorna o conjunto de nós alcançáveis seguindo as setas

    ranking.append({#Salva os indicadores da disciplina
        'codigo': codigo,
        'disciplina': grafo.nodes[codigo]['nome'],
        'dependentes_diretos': diretos,
        'dependentes_indiretos': total - diretos
        #todos os alcançáveis menos os dependentes diretos
        ,
        'alcance_total': total
    })

# Transforma a lista em uma tabela do Pandas na ordem das disciplinas com maior alcance total.
ranking = pd.DataFrame(ranking)
ranking = ranking.sort_values('alcance_total', ascending=False)
ranking.to_csv(saida / 'ranking_disciplinas.csv', index=False)#exporta a tabela


#Encontra o maior caminho de pré-requisitos
#representa etapas sucessivas de dependência.
cadeia = nx.dag_longest_path(grafo)
pd.DataFrame([
    {'ordem': i, 'codigo': codigo, 'disciplina': grafo.nodes[codigo]['nome']}
    for i, codigo in enumerate(cadeia, start=1)
]).to_csv(saida / 'maior_cadeia.csv', index=False)



#Definir posiçoes((x,y)necessário para ser desenhado) e tamanhos dos nós
posicoes = {}
for nivel in sorted(disciplinas['nivel'].unique()):#Cada nível separados em uma coluna no eixo x
    grupo = [c for c in grafo if grafo.nodes[c]['nivel'] == nivel] #Disciplinas daquele nível.
    grupo.sort(key=lambda c: grafo.out_degree(c), reverse=True) #Ordenados por quem tem mais dependentes diretos.
    #distribui as disciplinas verticalmente
    for i, codigo in enumerate(grupo):
        posicoes[codigo] = (nivel, (len(grupo) - 1) / 2 - i)

# Nós maiores = mais dependentes diretos.
tamanhos_nos = [260 + 110 * grafo.out_degree(c) for c in grafo]
#Guarda os códigos das cinco disciplinas com maior alcance total
principais = set(ranking.head(5)['codigo'])


#Plotagem da rede
def desenhar_rede(nome_arquivo, destacar_cadeia=False):
    fig, ax = plt.subplots(figsize=(25, 14))

    nx.draw_networkx_edges( #Desenho das arestas
        grafo, posicoes, ax=ax, arrows=True, arrowsize=9,
        edge_color='gray', alpha=0.23, width=1
    )

    if destacar_cadeia:
        cores = ['red' if c in cadeia else 'lightgray' for c in grafo]
         #Na figura cadeia, indicar em vermelho que pertence a maior cadeia
    else:
        cores = ['orange' if c in principais else 'steelblue' for c in grafo]
        # destacar em laranja se estiverr entre os cinco maiores alcances

     #Desenha os nós.
    nx.draw_networkx_nodes(
        grafo, posicoes, ax=ax, node_size=tamanhos_nos,
        node_color=cores, edgecolors='white', linewidths=1.2
    )

    if destacar_cadeia:#destaca as cadeias em vermelho
        nx.draw_networkx_edges(
            grafo, posicoes, ax=ax, edgelist=list(zip(cadeia, cadeia[1:])),
            edge_color='red', width=3, arrows=True, arrowsize=20
        )

    #Insere os códigos de cada disciplina nos nós.
    for codigo, (x, y) in posicoes.items():
        ax.annotate(
            codigo, (x, y), xytext=(0, 12), textcoords='offset points',
            ha='center', fontsize=9, fontweight='bold',
            bbox={'facecolor': 'white', 'edgecolor': 'none', 'alpha': 0.9}
        )

    titulo = 'Maior cadeia de pré-requisitos' if destacar_cadeia else 'Rede de pré-requisitos'
    ax.set_title(titulo + '\nTamanho do nó = dependentes diretos', fontsize=17)
    ax.axis('off')
    fig.savefig(saida / nome_arquivo, dpi=200, bbox_inches='tight')#Salvar a figuras em PNG
    plt.close(fig)


desenhar_rede('01_rede_completa.png')# Primeiramente: rede completa(com os cinco maiores alcances.)
desenhar_rede('02_maior_cadeia.png', destacar_cadeia=True)#Depois: rede com a maior cadeia destacada.


#Gerando Gráfico de barras com impacto direto e total
top10 = ranking.head(10).iloc[::-1] #dez maiores alcances.
fig, ax = plt.subplots(figsize=(13, 7))
y = range(len(top10))
#Em laranja: todos os dependentes alcançáveis.
ax.barh(y, top10['alcance_total'], label='Alcance total', color='orange')
#Em azul: dependentes diretos, sobreposta na mesma linha.
ax.barh(y, top10['dependentes_diretos'], label='Dependentes diretos', color='steelblue')
#Apresenta os códigos das disciplinas.
ax.set_yticks(list(y), top10['codigo'])
ax.set_xlabel('Número de disciplinas')
ax.set_title('Disciplinas com maior impacto na grade')
ax.legend()
fig.tight_layout()
fig.savefig(saida / '03_ranking_impacto.png', dpi=200)
plt.close(fig)

# 7. Mostrar os resultados no terminal
print('Disciplinas:', grafo.number_of_nodes())
print('Relações de pré-requisitos:', grafo.number_of_edges())
print('\nMaiores impactos (diretos e indiretos):')
print(ranking[['codigo', 'dependentes_diretos', 'alcance_total']].head(10).to_string(index=False))
print('\nMaior cadeia encontrada (', len(cadeia), 'disciplinas):', sep='')
for codigo in cadeia:
    print(' -', codigo, grafo.nodes[codigo]['nome'])
print('\nGráficos e CSVs salvos na pasta resultados.')
