## Respuestas a las preguntas teóricas 

1. Grafo de commits como DAG

    a. Demuestra que no existen ciclos en el grafo de commits de Git explicando el modelo de contenido inmutable de objetos.



    b. Analiza la complejidad de la búsqueda del critical merge path en un DAG con N nodos y M aristas

    Tenemos Dijkstra modificado con costos edge(merge=1, fast-forward=0)

    - Complejidad en el peor caso:

        Tiempo: O(M + N log N) usando heap binario

        M aristas (relaciones padre-hijo)
        N nodos (commits)
        log N por cada operación en priority queue


    - Peor caso específico para repositorios Git:

        Grafo denso: Cada commit es merge de todos los anteriores
        M ≈ N² en el peor caso (poco realista en Git)
        Complejidad real: O(N²) para grafos Git densos


2. DI, DIP e ISP
    
    a. Argumenta como la Dependency Injection en la micro-suite respeta el Dependency Inversion Principle y el Interface Segregation Principle, ejemplificando con tus clases de servicios y sus interfaces 

    

