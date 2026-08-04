# 面试题总结

## 一、AI 应用开发

### 1. LLM 基础

- **Q：什么是 Token？LLM 的上下文窗口限制对应用开发有什么影响？**
  - A：Token 是 LLM 处理文本的最小单位，英文约 1 词 = 1 Token，中文约 1 字 = 1.5~2 Token。上下文窗口限制决定了单次能处理的最大文本量，超出需要分段或摘要。常见模型的上下文窗口：GPT-4 约 128K，Claude 3 约 200K。

- **Q：Temperature 和 Top-P 参数对 LLM 输出有什么影响？**
  - A：Temperature 控制随机性，值越高输出越随机（创意场景用高值如 0.8，精确任务用低值如 0.2）。Top-P 是核采样，只从累计概率达到 P 的 token 中采样。两者一般只调一个。

- **Q：Prompt Engineering 有哪些常用技巧？**
  - A：Few-shot（给示例）、Chain-of-Thought（让模型逐步推理）、Role-playing（设定角色）、Output formatting（指定输出格式如 JSON）、Delimiters（用分隔符区分指令和内容）。

### 2. RAG（检索增强生成）

- **Q：RAG 的核心流程是什么？如何解决检索不相关的问题？**
  - A：核心流程：文档加载 → 切分 → 向量化 → 存储 → 检索 → 重排序 → 注入 Prompt → LLM 生成。解决检索不相关：Query 改写、混合检索（向量 + BM25）、重排序（Reranker）。

- **Q：文档切分（Chunking）策略有哪些？如何选择？**
  - A：固定长度切分（简单但可能切断语义）、递归字符切分（按段落/句子边界）、语义切分（按主题变化点）、重叠切分（相邻 chunk 有重叠避免信息丢失）。选择依据：文档类型、chunk 大小（一般 500-1000 token）、重叠比例（10%-20%）。

- **Q：向量数据库选型考虑哪些因素？**
  - A：数据规模（Chroma 适合小规模、Milvus/Qdrant 适合大规模）、检索性能（HNSW 索引 vs 暴力搜索）、过滤能力（标量+向量混合过滤）、部署方式（本地/云端）、生态集成（LangChain 支持度）。

- **Q：RAG 中的 Query 改写有哪些方法？**
  - A：HyDE（假设性文档嵌入，先让 LLM 生成假设答案再检索）、Multi-query（将一个问题拆成多个角度的子问题）、Step-back（抽象出更高层次的问题再检索）、Rewrite-Retrieve-Read（用 LLM 改写 query 后检索）。

### 3. Agent

- **Q：Agent 和普通 LLM 调用有什么区别？**
  - A：Agent = LLM + 工具调用 + 循环推理。普通调用是单次输入输出，Agent 能自主规划、调用工具、根据结果迭代直到完成任务。

- **Q：如何让 Agent 具备长期记忆能力？**
  - A：首先最基本是需要一个将会话消息持久化的存储机制，比如数据库或文件系统。然后是每次对话完成时对消息进行抽取摘要进行压缩，然后存储向量库，后续新对话来了之后根据用户问题进行检索，返回相关结果拼接到当前 Prompt 中作为上下文信息。最后就是一些细节的优化，比如 Token 限制、重复消息过滤、敏感信息脱敏、过期失效消息归档删除等。

- **Q：ReAct 是什么，说说它的原理？**
  - A：ReAct 本质上是一种提示工程范式，核心就是"思考（Thought）"和"行动（Action）"交替执行的循环系统。每次将思考的结果作为行动的输入，行动的结果作为思考的输入，直到完成任务。流程：Thought → Action → Observation → Thought → ... → Final Answer。

- **Q：多 Agent 协作有哪些模式？**
  - A：路由模式（一个 Agent 分发任务给专业 Agent）、协作模式（多个 Agent 共同完成一个任务，如一个写代码一个审查）、层级模式（Manager Agent 管理 Worker Agent）、辩论模式（多个 Agent 对同一问题给出不同观点，由裁判 Agent 决策）。

### 4. LangChain / LangGraph

- **Q：LangGraph 相比 LangChain 的 Chain 有什么优势？**
  - A：LangGraph 基于图结构，支持条件分支、循环、状态管理，适合复杂的多步 Agent 流程；Chain 是线性 DAG，灵活性不足。LangGraph 的核心概念：State（状态）、Node（节点）、Edge（边）、Conditional Edge（条件边）。

- **Q：LangChain 的 Callback 机制有什么用？**
  - A：Callback 用于监控和记录 LLM 调用过程，包括 token 使用量、延迟、中间步骤等。可用于日志记录、性能监控、成本统计、调试追踪。LangSmith 就是基于 Callback 实现的链路追踪。

### 5. MCP（Model Context Protocol）

- **Q：MCP 的作用是什么？和 Function Calling 有什么区别？**
  - A：MCP 是 Anthropic 提出的开放协议，标准化 LLM 与外部服务的交互。Function Calling 是单次工具调用，MCP 是持久化的服务连接，支持动态发现工具。类比：Function Calling 像 HTTP 请求，MCP 像 WebSocket 长连接。

- **Q：MCP 的架构是怎样的？**
  - A：MCP 采用 Client-Server 架构。MCP Host（如 Claude Desktop）包含 MCP Client，通过标准传输层（stdio/SSE）与 MCP Server 通信。Server 暴露 Resources（数据）、Tools（操作）、Prompts（模板）三种能力。

### 6. Skill 技能系统

- **Q：什么是渐进式披露（Progressive Disclosure）在 Agent 中的应用？**
  - A：Agent 启动时只加载所有 Skill 的 name + description（几百 token），匹配到相关任务时才动态加载完整的 SKILL.md 内容。好处：避免上下文膨胀，支持大量技能注册，按需加载节省 token。

---

## 二、Python

### 1. 基础语法

- **Q：Python 中 `is` 和 `==` 的区别？**
  - A：`==` 比较值是否相等，`is` 比较是否是同一个对象（内存地址）。小整数（-5~256）和短字符串会被 Python 缓存，`is` 可能返回 True，但不要依赖这个行为。

- **Q：Python 的 GIL 是什么？对多线程有什么影响？**
  - A：GIL（全局解释器锁）确保同一时刻只有一个线程执行 Python 字节码。影响：多线程无法真正并行执行 CPU 密集型任务。解决方案：多进程（multiprocessing）、C 扩展释放 GIL、asyncio 协程。

- **Q：深拷贝和浅拷贝的区别？**
  - A：浅拷贝（`copy.copy()`）只复制对象本身，内部引用不变；深拷贝（`copy.deepcopy()`）递归复制所有层级。注意：浅拷贝对不可变对象（如 tuple 中含 list）可能产生意外行为。

### 2. 异步编程

- **Q：Python 的 async/await 和多线程有什么区别？适用场景？**
  - A：async/await 是协程，单线程内通过事件循环切换，适合 I/O 密集型（网络请求、数据库）；多线程适合 CPU 密集型任务（但受 GIL 限制）。协程切换成本远低于线程。

- **Q：`asyncio.gather()` 和 `asyncio.create_task()` 有什么区别？**
  - A：`gather()` 并发执行多个协程并等待全部完成，返回结果列表；`create_task()` 立即调度协程执行，返回 Task 对象可单独管理。`gather()` 适合"全部完成才继续"，`create_task()` 适合"后台执行"。

- **Q：FastAPI 的依赖注入是怎么实现的？**
  - A：通过 `Depends()` 声明依赖，FastAPI 自动解析依赖图并注入。支持嵌套依赖、异步依赖、生成器依赖（`yield` 实现资源清理，类似 Java 的 `@PreDestroy`）。

### 3. 装饰器

- **Q：请手写一个带参数的装饰器。**
  ```python
  def retry(max_times=3):
      def decorator(func):
          def wrapper(*args, **kwargs):
              for i in range(max_times):
                  try:
                      return func(*args, **kwargs)
                  except Exception as e:
                      if i == max_times - 1:
                          raise e
          return wrapper
      return decorator
  ```

- **Q：`functools.lru_cache` 和 `functools.cache` 有什么区别？**
  - A：`lru_cache(maxsize=128)` 有容量限制，超出后淘汰最久未使用的；`cache()` 无容量限制（Python 3.9+）。注意：缓存可变对象（如 list、dict）作为参数时会出错，因为 list 不可 hash。

### 4. 面向对象

- **Q：Python 的 `__slots__` 有什么用？**
  - A：限制实例只能有指定的属性，节省内存（不创建 `__dict__`），同时防止动态添加属性。适合大量实例的场景（如 ORM 模型）。

- **Q：`@property` 装饰器的作用？和 Java 的 Getter/Setter 有什么区别？**
  - A：`@property` 将方法伪装成属性访问，可以添加验证逻辑。Java 需要显式写 getter/setter 方法，Python 用 `@property` 更简洁，调用方无感知（`obj.name` 而非 `obj.getName()`）。

### 5. 包管理

- **Q：`requirements.txt`、`Pipfile`、`pyproject.toml` 有什么区别？**
  - A：`requirements.txt` 是 pip 的标准格式，简单但无依赖分组；`Pipfile` 是 Pipenv 的格式，支持开发/生产依赖分组；`pyproject.toml` 是 PEP 518 标准，Poetry/uv 等现代工具使用，支持构建配置。

---

## 三、Java 后端

### 1. Spring Boot

- **Q：Spring Boot 的自动配置原理是什么？**
  - A：通过 `@EnableAutoConfiguration` 读取 `META-INF/spring.factories`（Spring Boot 2.x）或 `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports`（3.x）中的配置类，结合 `@Conditional` 注解按需加载 Bean。

- **Q：Spring 中 `@Autowired` 和 `@Resource` 有什么区别？**
  - A：`@Autowired` 是 Spring 注解，按类型注入；`@Resource` 是 JSR-250 标准，按名称注入（名称找不到再按类型）。推荐用构造器注入（`@RequiredArgsConstructor` + `final`），便于测试和不可变性。

- **Q：Spring Boot 的 Starter 机制是什么？**
  - A：Starter 是一组依赖的集合 + 自动配置类。引入 starter 后自动引入相关依赖并自动配置 Bean。自定义 Starter：创建 `xxx-spring-boot-starter` 模块，编写自动配置类 + `spring.factories` 注册。

### 2. JVM

- **Q：JVM 内存模型分为哪几个区域？各自的作用？**
  - A：堆（对象实例，GC 主要区域）、方法区/元空间（类信息、常量）、虚拟机栈（方法调用帧）、本地方法栈（Native 方法）、程序计数器（当前执行指令）。

- **Q：常见的 GC 算法有哪些？G1 收集器的特点？**
  - A：算法：标记-清除、标记-整理、复制算法。G1 特点：将堆分为多个 Region，可预测停顿时间（`-XX:MaxGCPauseMillis`），适合大堆（6GB+），同时收集 Young 和 Old 区。

- **Q：类加载机制是什么？双亲委派模型？**
  - A：类加载过程：加载 → 验证 → 准备 → 解析 → 初始化。双亲委派：子加载器先委托父加载器加载，父加载器无法加载时才自己加载。好处：防止核心类被篡改，避免类重复加载。打破方式：SPI 机制（Thread.currentThread().getContextClassLoader()）。

### 3. 并发编程

- **Q：`synchronized` 和 `ReentrantLock` 的区别？**
  - A：`synchronized` 是 JVM 内置锁，自动释放；`ReentrantLock` 是 API 级别锁，支持公平锁、可中断、超时等高级特性。Java 6 之后 `synchronized` 做了大量优化（偏向锁、轻量级锁），性能差距不大。

- **Q：`volatile` 关键字的作用？**
  - A：保证可见性（一个线程修改后其他线程立即可见）和有序性（禁止指令重排序），不保证原子性。典型场景：DCL 单例模式中的实例变量、状态标志位。

- **Q：线程池的核心参数有哪些？如何合理配置？**
  - A：7 个参数：corePoolSize、maximumPoolSize、keepAliveTime、unit、workQueue、threadFactory、handler。配置原则：CPU 密集型 = CPU 核数 + 1，IO 密集型 = CPU 核数 × 2 或更多。拒绝策略：AbortPolicy（默认抛异常）、CallerRunsPolicy（调用者执行）、DiscardPolicy（丢弃）。

### 4. 设计模式

- **Q：你在项目中用过哪些设计模式？请举例说明。**
  - A：策略模式（不同 LLM 适配器实现同一接口）、工厂模式（依赖注入容器创建 Service 实例）、观察者模式（事件监听通知）、模板方法（Service 抽象类定义流程，子类实现具体步骤）、适配器模式（统一不同 LLM API 的调用方式）。

- **Q：Spring 中用到了哪些设计模式？**
  - A：工厂模式（BeanFactory）、单例模式（默认 Bean 单例）、代理模式（AOP）、观察者模式（ApplicationEvent）、模板方法（JdbcTemplate）、适配器模式（HandlerAdapter）。

---

## 四、Vue 前端

### 1. 基础概念

- **Q：Vue 2 和 Vue 3 的主要区别？**
  - A：Vue 3 使用 Composition API（`setup()`）、Proxy 替代 Object.defineProperty 实现响应式、支持 Tree-shaking、TypeScript 支持更好、Fragment/Teleport/Suspense 新组件。

- **Q：Vue 的响应式原理是什么？**
  - A：Vue 2 用 `Object.defineProperty` 劫持 getter/setter，无法检测属性新增/删除和数组索引变化。Vue 3 用 `Proxy` 代理整个对象，可以拦截所有操作，性能更好。

### 2. 状态管理

- **Q：Vuex 和 Pinia 有什么区别？为什么推荐 Pinia？**
  - A：Pinia 去掉了 Mutation，直接修改 state；支持 Composition API；TypeScript 支持更好；更轻量；支持多 store 实例。Vuex 需要 Mutation 修改 state，TypeScript 支持差。

### 3. 性能优化

- **Q：Vue 项目有哪些常见的性能优化手段？**
  - A：路由懒加载（`() => import()`）、组件懒加载（`defineAsyncComponent`）、`v-show` vs `v-if`（频繁切换用 v-show）、虚拟列表（`vue-virtual-scroller`）、图片懒加载、打包优化（splitChunks、CDN 外部化）、`keep-alive` 缓存组件。

- **Q：`v-if` 和 `v-show` 的区别？使用场景？**
  - A：`v-if` 真正销毁/创建 DOM，切换开销大；`v-show` 只是切换 CSS display，初始渲染开销大。频繁切换用 `v-show`，条件很少改变用 `v-if`。

---

## 五、MySQL

### 1. 索引

- **Q：什么是覆盖索引？什么情况下索引会失效？**
  - A：覆盖索引：查询的列都在索引中，无需回表。索引失效：左模糊查询（`LIKE '%xxx'`）、对索引列做函数运算、隐式类型转换、`OR` 条件中有非索引列、`!=` 或 `<>`、`IS NULL`/`IS NOT NULL`（视数据分布）。

- **Q：聚簇索引和非聚簇索引的区别？**
  - A：聚簇索引（InnoDB 主键索引）：叶子节点存储完整行数据，一张表只有一个。非聚簇索引（二级索引）：叶子节点存储主键值，需要回表查询。这就是为什么 InnoDB 推荐用自增主键（避免页分裂）。

- **Q：联合索引的最左前缀原则是什么？**
  - A：联合索引 `(a, b, c)`，查询条件必须从最左列开始连续匹配。`WHERE a=1 AND b=2` 可以用索引，`WHERE b=2 AND c=3` 不能用（跳过了 a）。但 MySQL 8.0 的优化器会自动调整 `AND` 条件的顺序。

### 2. 事务

- **Q：MySQL 事务的隔离级别有哪些？默认是哪个？**
  - A：读未提交（脏读）、读已提交（不可重复读）、可重复读（默认，幻读）、串行化。InnoDB 通过 MVCC + Next-Key Lock 在可重复读级别下解决了大部分幻读问题。

- **Q：MVCC 是什么？原理是什么？**
  - A：MVCC（多版本并发控制）通过隐藏列（事务 ID、回滚指针）和 Undo Log 实现。读操作读快照（Read View），写操作写新版本。好处：读写不阻塞，提高并发性能。

### 3. 锁

- **Q：行锁和表锁的区别？什么情况下行锁会退化为表锁？**
  - A：行锁锁单行，表锁锁整表。行锁退化：索引失效时（全表扫描）、范围查询过大时、`UPDATE` 无索引条件时。InnoDB 的行锁是加在索引上的，不是数据行上。

- **Q：什么是死锁？如何避免？**
  - A：死锁：两个事务互相等待对方释放锁。避免：按固定顺序加锁、缩短事务时间、降低隔离级别、设置锁等待超时（`innodb_lock_wait_timeout`）。

### 4. 优化

- **Q：慢 SQL 如何排查和优化？**
  - A：开启慢查询日志（`long_query_time=1`）→ `EXPLAIN` 分析执行计划（关注 type、key、rows、Extra）→ 检查索引使用 → 优化 SQL 写法（避免 `SELECT *`、子查询改 JOIN）→ 考虑分库分表。

- **Q：`EXPLAIN` 结果中 type 字段的含义？**
  - A：从好到差：system > const > eq_ref > ref > range > index > ALL。一般要求至少达到 range 级别，ref 及以上为优秀。

---

## 六、Redis

### 1. 数据结构

- **Q：Redis 有哪些数据结构？各自的使用场景？**
  - A：String（缓存、计数器）、Hash（对象存储，如用户信息）、List（消息队列、最新列表）、Set（去重、共同好友）、ZSet（排行榜、延迟队列）、Bitmap（签到、在线状态）、HyperLogLog（UV 统计）、GEO（地理位置）。

- **Q：Redis 的 String 和 Java 的 String 有什么区别？**
  - A：Redis 的 String 是二进制安全的，可以存储任意数据（文本、序列化对象、图片），最大 512MB。本质是 SDS（Simple Dynamic String），预分配空间减少内存重分配。

### 2. 持久化

- **Q：RDB 和 AOF 的区别？如何选择？**
  - A：RDB 是快照（`bgsave` fork 子进程写文件），恢复快但可能丢数据；AOF 记录每条写命令（`appendfsync` 策略：always/everysec/no），数据完整但文件大、恢复慢。通常两者结合使用，Redis 4.0+ 支持混合持久化（RDB + AOF 增量）。

### 3. 缓存问题

- **Q：什么是缓存穿透、缓存击穿、缓存雪崩？如何解决？**
  - A：
    - 穿透（查不存在的数据，请求直接打到 DB）→ 布隆过滤器、缓存空值（设短过期时间）
    - 击穿（热点 key 过期瞬间大量请求打到 DB）→ 互斥锁（`SETNX`）、逻辑过期（后台异步更新）
    - 雪崩（大量 key 同时过期或 Redis 宕机）→ 随机过期时间、多级缓存、限流降级

### 4. 分布式锁

- **Q：Redis 如何实现分布式锁？有什么问题？**
  - A：`SET key value NX EX seconds`。问题：主从切换锁丢失（Redlock 解决，但争议大）、锁超时业务未完成（看门狗续期，Redisson 实现）、时钟漂移。替代方案：ZooKeeper（强一致但性能低）、etcd。

- **Q：Redisson 的看门狗机制是什么？**
  - A：获取锁时设置默认 30 秒过期时间，同时启动后台线程每 10 秒（1/3 过期时间）续期，只要线程还持有锁就不断续期。释放锁时停止续期线程。

---

## 七、计算机网络

### 1. HTTP

- **Q：HTTP 和 HTTPS 的区别？HTTPS 的握手过程？**
  - A：HTTPS = HTTP + TLS/SSL 加密。握手：客户端发 ClientHello（支持的加密套件）→ 服务端返回 ServerHello + 证书 → 客户端验证证书并生成会话密钥（用服务端公钥加密）→ 双方用会话密钥加密通信。

- **Q：HTTP 1.1、2.0、3.0 的区别？**
  - A：1.1：持久连接、管道化（有头端阻塞）；2.0：多路复用、头部压缩、服务器推送（基于 TCP）；3.0：基于 QUIC（UDP），解决 TCP 队头阻塞，0-RTT 建连。

- **Q：GET 和 POST 的区别？**
  - A：GET 参数在 URL 中，有长度限制，可缓存，可收藏；POST 参数在请求体中，无长度限制，不可缓存。语义上：GET 是安全的（不修改资源），POST 是不安全的。

### 2. TCP

- **Q：TCP 三次握手和四次挥手的过程？为什么挥手需要四次？**
  - A：握手：SYN → SYN+ACK → ACK。挥手：FIN → ACK → FIN → ACK。挥手需要四次因为 TCP 是全双工，双方需要各自关闭连接（收到 FIN 只表示对方不再发送，但我方可能还有数据要发）。

- **Q：TCP 和 UDP 的区别？各自的使用场景？**
  - A：TCP 可靠、有序、面向连接，适合文件传输、网页浏览；UDP 不可靠、无序、无连接，适合视频直播、DNS 查询、游戏。TCP 有拥塞控制（慢开始、拥塞避免、快重传、快恢复）。

---

## 八、操作系统

### 1. 进程与线程

- **Q：进程和线程的区别？协程和线程的区别？**
  - A：进程是资源分配单位（独立内存空间），线程是调度单位（共享进程资源）。协程是用户态线程，切换成本更低（无需内核态切换），由程序控制而非操作系统。Python 的 asyncio、Go 的 goroutine 都是协程。

- **Q：进程间通信（IPC）有哪些方式？**
  - A：管道（Pipe）、消息队列、共享内存（最快）、信号量、信号、Socket。共享内存需要配合同步机制（信号量/互斥锁）使用。

### 2. 内存管理

- **Q：虚拟内存的作用？页面置换算法有哪些？**
  - A：虚拟内存让程序使用比物理内存更大的地址空间，提供内存保护和隔离。置换算法：FIFO（简单但 Belady 异常）、LRU（最常用，最近最少使用）、LFU（最不经常使用）、Clock（NRU 近似 LRU）。

- **Q：什么是内存泄漏？如何排查？**
  - A：程序分配了内存但未释放，导致可用内存逐渐减少。Java：JVM 自动 GC，但对象被意外引用导致无法回收（如静态集合持续增长）。排查：jmap 导出堆快照 → MAT/JProfiler 分析 → 找 GC Root 引用链。

---

## 九、设计模式与架构

### 1. 设计原则

- **Q：SOLID 原则分别是什么？**
  - A：S-单一职责（一个类只有一个变化原因）、O-开闭原则（对扩展开放，对修改关闭）、L-里氏替换（子类可替换父类）、I-接口隔离（客户端不依赖不需要的接口）、D-依赖倒置（依赖抽象而非具体实现）。

- **Q：开闭原则在实际项目中怎么体现？**
  - A：比如 LLM 适配器：定义 `LlmPort` 接口（抽象），OpenAI、阿里云、豆包各自实现。新增模型时只需新增实现类，不需要修改已有代码。这就是对扩展开放、对修改关闭。

### 2. 微服务

- **Q：微服务架构的优势和问题？如何保证服务间数据一致性？**
  - A：优势：独立部署、技术异构、弹性伸缩、团队自治。问题：分布式事务、服务治理复杂、运维成本高、网络延迟。一致性方案：Saga 模式（长事务拆成多个本地事务）、事件溯源（Event Sourcing）、TCC（Try-Confirm-Cancel）、可靠消息最终一致性。

- **Q：服务注册与发现是怎么实现的？**
  - A：服务启动时向注册中心（Nacos/Eureka/Consul）注册自己的地址，消费者从注册中心获取可用实例列表。负载均衡策略：轮询、随机、权重、一致性哈希。健康检查：心跳机制，超时未心跳则剔除。

### 3. 常用设计模式

- **Q：策略模式和工厂模式的区别？结合使用场景？**
  - A：策略模式：定义一组算法，运行时选择（如不同 LLM 适配器）。工厂模式：创建对象的接口，子类决定创建哪个（如依赖注入容器）。结合：工厂根据配置创建对应的策略实现。

- **Q：观察者模式和发布订阅模式有什么区别？**
  - A：观察者模式：Subject 直接通知 Observer（紧耦合，如 Java 的 `Observable`）。发布订阅：通过消息中间件（Broker）解耦，Publisher 和 Subscriber 互不知晓（如 Redis Pub/Sub、Kafka）。

---

## 十、项目经验（通用）

### 1. 项目介绍

- **Q：请介绍一下你最近做的项目？你在其中负责什么？**
  - A：STAR 法则回答：Situation（背景：公司需要 AI 对话系统）→ Task（任务：负责架构设计和核心模块开发）→ Action（行动：采用三层架构，实现 RAG + Agent + Skill 系统）→ Result（结果：支持多模型切换，知识库检索准确率提升 XX%）。

### 2. 技术难点

- **Q：项目中遇到的最大技术挑战是什么？如何解决的？**
  - A：描述问题（如 RAG 检索不相关）→ 分析原因（向量检索语义匹配但关键词不匹配）→ 尝试方案（混合检索：向量 + BM25 + Reranker）→ 最终解决（检索准确率从 60% 提升到 85%）→ 总结经验。

### 3. 性能优化

- **Q：你做过哪些性能优化？效果如何？**
  - A：量化回答：优化前 QPS/响应时间 → 优化手段（如数据库加索引、Redis 缓存热点数据、异步处理非关键路径）→ 优化后指标提升（响应时间从 500ms 降到 50ms，QPS 从 100 提升到 1000）。

### 4. 架构设计

- **Q：你的项目为什么采用三层架构？**
  - A：API 层负责接口和参数校验，Application 层负责业务逻辑编排，Infrastructure 层封装外部依赖。好处：职责清晰、易于测试（Mock Infrastructure）、易于替换（如换 LLM 供应商只改 Adapter）、符合依赖倒置原则。

### 5. 团队协作

- **Q：你们团队是怎么协作的？代码管理流程？**
  - A：Git Flow：main（生产）→ develop（开发）→ feature（功能分支）。Code Review：PR 至少一人审批。CI/CD：提交代码自动跑测试和 lint，通过后自动部署到测试环境。
