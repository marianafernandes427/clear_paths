# clear_paths
# Clear Paths Guimarães

Projeto desenvolvido no âmbito da unidade curricular de Inteligência Artificial, com o objetivo de modelar e resolver um problema de planeamento de rotas pedonais acessíveis na cidade de Guimarães.

## Objetivo

O sistema recomenda percursos pedonais entre dois pontos da cidade, considerando critérios como distância, acessibilidade, inclinação, ruído, qualidade do ar, meteorologia e perfil do utilizador.

## Cidade de estudo

Guimarães, Portugal.

Exemplos de pontos usados:
- Universidade do Minho - Campus de Azurém
- Largo do Toural
- Estação CP de Guimarães
- Castelo de Guimarães
- Centro Cultural Vila Flor

## Fontes de dados

Os dados utilizados provêm de fontes reais:

- OpenStreetMap, para a rede pedonal e atributos das ruas
- IPMA, para meteorologia
- Câmara Municipal de Guimarães, para WebSIG e mapa de ruído
- Estação de qualidade do ar de Azurém / APA QUALAR
- Copernicus DEM ou DGT, para elevação e inclinação

A descrição das fontes encontra-se em:

```text
data/metadata/fontes_dados.csv
