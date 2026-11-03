# Una IA que lee mamografías

Demo educativo en Streamlit. Una red neuronal (ensemble de 3 EfficientNet-B0) clasifica hallazgos
mamográficos como benignos o malignos y muestra con un mapa de calor (Grad-CAM) en qué parte de la
imagen se fijó. La app muestra los resultados ya calculados sobre una **prueba sellada de 163 mamas**
que el modelo nunca vio; no ejecuta el modelo, así que carga rápido en cualquier equipo.

## Qué incluye

- **Mira un caso:** dos vistas de cada mama, con o sin mapa de calor, la probabilidad según la IA,
  su decisión y el diagnóstico por biopsia. Tiene un **modo adivinanza** que oculta las respuestas
  hasta pulsar «Revelar».
- **¿Qué tan bien funciona?:** malignos detectados, falsas alarmas, AUC y comparación con la edad.
- **¿Mira donde debe?:** resultados del *pointing game* en VinDr-Mammo (solo cifras agregadas).
- **Lo que esta IA no hace:** sus limitaciones.

## Ejecutar

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Resultados principales (prueba sellada, CMMD)

| Métrica | Valor |
|---|---|
| AUC | 0.80 (IC95% 0.73–0.86) |
| AUC usando solo la edad | 0.65 |
| Sensibilidad (umbral fijado en validación para ≥90%) | 78/84 = 93% |
| Especificidad | 25/79 = 32% |
| Pointing game en VinDr-Mammo (BI-RADS 4–5) | 60% de aciertos frente a 10% al azar |

## Datos y licencias

- **Imágenes:** *The Chinese Mammography Database (CMMD)*, The Cancer Imaging Archive,
  DOI [10.7937/tcia.eqde-4b16](https://doi.org/10.7937/tcia.eqde-4b16), licencia
  [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Las imágenes (empaquetadas en `datos/imagenes.zip`) fueron
  recortadas, reducidas y tienen mapas Grad-CAM superpuestos.
- **Prueba de localización:** VinDr-Mammo (PhysioNet). Su acuerdo de uso no permite redistribuir las
  imágenes, por lo que aquí solo se publican resultados agregados (`datos/vindr_pointing.json`).

## Aviso

Demo educativo elaborado por Alonzo Encarnación. No es un dispositivo médico, no hace tamizaje y no
sustituye la biopsia ni el criterio del radiólogo.
