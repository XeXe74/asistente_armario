# Asistente de armario: notas de diseño y decisiones

## El proyecto

Estamos construyendo un asistente de armario conversacional que combina visión por computador y voz. La cámara reconoce en tiempo real la prenda que llevamos puesta (tipo y color). Por voz pedimos una prenda de nuestro armario que combine con ella y podemos matizar la petición ("algo más informal", "otra"). El sistema busca en un armario catalogado previamente con fotos y muestra la sugerencia como imagen, junto con el motivo de la elección.

Queremos resolver la decisión diaria de qué ponerse. Las apps de armario digital ya catalogan la ropa, pero no saben qué llevamos puesto y obligan a introducirlo a mano. Ese es el hueco que cubrimos.

## Por qué visión y voz (Vía A)

Cada modalidad aporta algo que la otra no puede dar. La cámara da el contexto objetivo (qué llevamos) sin tener que describirlo, y la voz da la intención y el matiz de la búsqueda, que la imagen no puede inferir. El ejemplo más claro de fusión es la deixis: en "¿qué pantalón va con esto?", el "esto" lo resuelve la cámara.

## Arquitectura

Organizamos el sistema en cuatro capas: percepción (visión y voz), diálogo y fusión, recomendación y presentación. Los módulos solo se comunican mediante estructuras de datos compartidas (observación visual, intención, prenda y sugerencia), así que podemos desarrollar y probar cada uno por separado con datos simulados. El núcleo es una máquina de estados explícita que reproduce nuestro diagrama de flujo. Funciona por eventos: la cámara se ejecuta continuamente en su propio hilo y la voz se activa pulsando una tecla para hablar (*push-to-talk*).

Todo se ejecuta en local y es gratuito. La configuración (umbrales, cámara, modelos) va en un fichero aparte, fuera del código, y las dependencias están fijadas para que cualquiera pueda ejecutarlo siguiendo el README.

## Visión

Usamos YOLO con pesos ya entrenados en DeepFashion2 para localizar las prendas sobre personas reales. Así distinguimos la parte de arriba de la de abajo y funciona en tiempo real en CPU. Como las clases de DeepFashion2 son genéricas y no incluyen el color, sobre cada recorte aplicamos CLIP en modo zero-shot para el tipo concreto (camisa, sudadera, jersey…) y k-means para extraer el color dominante. Suavizamos las predicciones a lo largo de varios fotogramas para obtener una confianza estable, y esa confianza decide si el sistema pide confirmación al usuario.

## Voz

Transcribimos con faster-whisper en local. Para interpretar la petición usamos un LLM local mediante Ollama, que solo extrae la intención en un JSON con estructura fija (categoría, formalidad, color, "otra"). El LLM nunca elige prendas, para que no invente ninguna que no tengamos. Las órdenes cortas ("sí", "no", "otra") pasan por reglas, y las reglas también sirven de respaldo si el LLM falla o tarda demasiado. Las respuestas del sistema también se dan por voz (TTS), lo que mejora la accesibilidad.

## Fusión

Hemos definido una política explícita para cada situación de conflicto o ausencia. Si la visión tiene poca confianza, el sistema pregunta y el usuario puede confirmar o corregir hablando. Si la voz contradice a la visión, gana la visión cuando su confianza es alta y, si no, se pide aclaración. Si no se entiende la voz, el sistema pide repetir y después ofrece alternativa por teclado. Si no hay prendas compatibles, relaja una restricción y lo comunica. El contexto guarda el historial de sugerencias rechazadas y de matices, y eso nos permite adaptar las respuestas al usuario.

## Recomendación

Hemos optado por un recomendador híbrido. La compatibilidad entre prendas (categoría complementaria, armonía de color y formalidad) se decide con reglas, porque no tenemos datos etiquetados de outfits y porque así podemos explicar cada sugerencia. CLIP lo usamos solo para comparar el matiz pedido por voz con las prendas (texto con imagen), no para comparar prendas entre sí: CLIP mide parecido, no compatibilidad.

## Catálogo

Damos de alta las prendas con un script que procesa sus fotos usando los mismos modelos que la visión en vivo, para que las etiquetas coincidan. El resultado es un catálogo en JSON que se puede corregir a mano. De forma opcional, entrenaremos un clasificador lineal sobre los embeddings de CLIP con el dataset Fashion Product Images para predecir la formalidad de cada prenda. Ese mismo dataset nos servirá para medir la precisión de CLIP con nuestras categorías.

## Datos y ética

Las imágenes de la cámara se procesan en memoria y nunca se guardan, y ningún dato sale del ordenador. Las fotos del armario son de prendas, no de personas. Cuando la confianza es baja, el sistema lo muestra en lugar de presentar la predicción como cierta.

## Lo que hemos descartado

Descartamos el espejo virtual con superposición realista de la ropa, porque es un problema de síntesis de imagen demasiado ambicioso sin GPU. Lo dejamos como posible mejora en forma de pegatina 2D. Descartamos entrenar nuestro propio recomendador, porque no tenemos datos y los datasets de outfits no se parecen a nuestras imágenes. También descartamos las APIs comerciales y la Web Speech API del navegador, porque envían datos a terceros, y Fashion-MNIST, por su baja resolución y porque no tiene color.

