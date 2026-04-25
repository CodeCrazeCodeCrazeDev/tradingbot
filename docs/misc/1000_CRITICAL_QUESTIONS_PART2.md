# 1,000 CRITICAL QUESTIONS - PART 2

## SECTION 2 (Continued): DATA INGESTION, QUALITY, LINEAGE & CORRUPTION

### Data Storage

101. What is your data retention policy, and what happens when storage is exhausted?
102. How do you handle storage failures during write operations?
103. What is your strategy for archiving data that is no longer actively used?
104. How do you ensure data consistency across distributed storage?
105. What happens when storage latency exceeds acceptable thresholds?
106. How do you handle storage that becomes read-only due to quota limits?
107. What is your backup strategy, and how often do you test restores?
108. How do you handle storage encryption key rotation?
109. What happens when storage replication lag causes inconsistent reads?
110. How do you detect when storage is silently dropping writes?

### Real-Time Data Processing

111. What is the maximum acceptable latency for real-time data processing?
112. How do you handle bursts of data that exceed processing capacity?
113. What happens when real-time processing falls behind and data accumulates?
114. How do you prioritize data processing when resources are constrained?
115. What is your strategy for handling data that arrives faster than it can be persisted?
116. How do you detect when real-time processing is producing incorrect results?
117. What happens when real-time and batch processing produce different results?
118. How do you handle real-time data that requires historical context to interpret?
119. What is your strategy for replaying real-time data for debugging?
120. How do you test real-time processing under realistic load conditions?

### Data Validation

121. What validation rules do you apply to incoming data, and are they sufficient?
122. How do you handle data that passes validation but is still incorrect?
123. What happens when validation rules are too strict and reject valid data?
124. How do you update validation rules without disrupting live processing?
125. What is your strategy for validating data that has complex interdependencies?
126. How do you detect when validation rules themselves are incorrect?
127. What happens when validation is too slow and creates a bottleneck?
128. How do you handle validation failures gracefully without losing data?
129. What is your strategy for validating data from untrusted sources?
130. How do you test validation rules for completeness and correctness?

---

## SECTION 3: MARKET MICROSTRUCTURE & EXECUTION REALISM (Questions 131-200)

### Order Book Dynamics

131. How do you model the impact of your orders on the order book?
132. What happens when the order book is thin and your order would move the market?
133. How do you detect when order book data is stale or incomplete?
134. What is your strategy for handling order book updates that arrive out of order?
135. How do you model hidden liquidity that doesn't appear in the visible order book?
136. What happens when the order book shows liquidity that disappears when you try to take it?
137. How do you handle order books with different tick sizes across venues?
138. What is your strategy for detecting spoofing and layering in the order book?
139. How do you model the queue position of your limit orders?
140. What happens when order book depth changes dramatically between signal and execution?

### Execution Quality

141. How do you measure execution quality, and what metrics do you track?
142. What is your expected slippage model, and how do you validate it?
143. How do you detect when execution quality is degrading over time?
144. What happens when your execution consistently underperforms your model?
145. How do you handle partial fills and their impact on strategy performance?
146. What is your strategy for handling fills at prices worse than expected?
147. How do you model the probability of fill for limit orders?
148. What happens when fill rates drop below acceptable thresholds?
149. How do you handle execution during periods of extreme volatility?
150. What is your strategy for detecting and avoiding toxic order flow?

### Latency

151. What is your end-to-end latency from signal to order acknowledgment?
152. How do you detect when latency spikes occur, and what causes them?
153. What happens when latency exceeds the validity window of your signal?
154. How do you handle latency differences across multiple venues?
155. What is your strategy for minimizing latency in critical execution paths?
156. How do you detect when network latency is causing missed opportunities?
157. What happens when latency is asymmetric (fast to send, slow to receive)?
158. How do you handle latency introduced by your own processing?
159. What is your strategy for measuring and reducing serialization latency?
160. How do you test the system under realistic latency conditions?

### Market Impact

161. How do you model the permanent vs. temporary market impact of your trades?
162. What is the maximum position size before market impact becomes unacceptable?
163. How do you detect when your trading is moving the market?
164. What happens when market impact exceeds your model predictions?
165. How do you adjust execution strategy based on real-time market impact?
166. What is your strategy for minimizing information leakage during execution?
167. How do you handle market impact in illiquid markets?
168. What happens when other participants detect and front-run your orders?
169. How do you model market impact across correlated instruments?
170. What is your strategy for measuring market impact after the fact?

### Venue Selection

171. How do you choose which venue to route orders to?
172. What happens when your preferred venue is unavailable?
173. How do you handle venues with different fee structures?
174. What is your strategy for handling venues with different order types?
175. How do you detect when a venue is providing inferior execution?
176. What happens when venue selection logic makes suboptimal choices?
177. How do you handle venues with different settlement times?
178. What is your strategy for handling venues in different regulatory jurisdictions?
179. How do you model the probability of fill across different venues?
180. What happens when venue connectivity is degraded but not completely down?

### Order Types & Execution Algorithms

181. What order types do you use, and why?
182. How do you handle order types that behave differently across venues?
183. What happens when an order type is not supported by a venue?
184. How do you choose between aggressive and passive execution?
185. What is your strategy for handling order amendments and cancellations?
186. How do you detect when order amendments are failing silently?
187. What happens when cancel requests are not acknowledged?
188. How do you handle orders that are partially filled before cancellation?
189. What is your strategy for handling order expiration?
190. How do you test execution algorithms under realistic conditions?

### Execution Risk

191. What happens when you have orders in flight during a market halt?
192. How do you handle execution during market opens and closes?
193. What is your strategy for handling execution during circuit breakers?
194. How do you detect when execution is failing systematically?
195. What happens when execution errors accumulate faster than you can handle them?
196. How do you handle execution in markets with different trading hours?
197. What is your strategy for handling execution during corporate actions?
198. How do you detect when execution is being manipulated by the venue?
199. What happens when execution reports are delayed or missing?
200. How do you reconcile executed trades with expected trades?

---

## SECTION 4: STRATEGY DESIGN, VALIDATION & RETIREMENT (Questions 201-270)

### Strategy Development

201. What is your process for generating strategy hypotheses?
202. How do you prevent overfitting during strategy development?
203. What is your criteria for determining if a strategy is worth testing?
204. How do you handle strategies that work in backtests but fail in paper trading?
205. What is your process for iterating on strategy parameters?
206. How do you detect when strategy development is chasing noise?
207. What happens when a strategy requires data you don't have?
208. How do you handle strategies that require capabilities you haven't built?
209. What is your strategy for managing multiple concurrent strategy development efforts?
210. How do you document strategy development decisions for future reference?

### Strategy Validation

211. What is your out-of-sample testing methodology?
212. How do you prevent data leakage between training and testing?
213. What statistical tests do you apply to validate strategy performance?
214. How do you handle strategies that pass statistical tests but have poor economics?
215. What is your criteria for promoting a strategy from research to paper trading?
216. How do you validate that strategy performance is not due to luck?
217. What happens when validation results are ambiguous?
218. How do you handle strategies that validate well on some metrics but not others?
219. What is your process for stress testing strategies before deployment?
220. How do you validate strategy behavior under extreme market conditions?

### Strategy Deployment

221. What is your process for deploying a new strategy to production?
222. How do you handle strategy deployment failures?
223. What is your strategy for ramping up capital allocation to new strategies?
224. How do you monitor newly deployed strategies for unexpected behavior?
225. What happens when a newly deployed strategy immediately loses money?
226. How do you handle strategies that require warm-up periods?
227. What is your process for coordinating strategy deployment with risk limits?
228. How do you handle strategies that interact with each other?
229. What happens when strategy deployment causes system instability?
230. How do you rollback a strategy deployment that goes wrong?

### Strategy Monitoring

231. What metrics do you track for each strategy in production?
232. How do you detect when a strategy is underperforming its expectations?
233. What is your threshold for investigating strategy performance issues?
234. How do you distinguish between normal variance and strategy degradation?
235. What happens when strategy monitoring itself fails?
236. How do you handle strategies that perform well overall but have bad periods?
237. What is your process for investigating strategy anomalies?
238. How do you detect when strategy behavior has changed without parameter changes?
239. What happens when multiple strategies degrade simultaneously?
240. How do you monitor strategy interactions and correlations?

### Strategy Retirement

241. What is your criteria for retiring a strategy?
242. How do you handle strategies that are profitable but declining?
243. What is your process for gracefully unwinding strategy positions?
244. How do you handle strategies that cannot be retired due to illiquid positions?
245. What happens when a retired strategy's positions are still open?
246. How do you preserve strategy artifacts for future analysis?
247. What is your process for learning from retired strategies?
248. How do you handle strategies that should be retired but are politically protected?
249. What happens when strategy retirement causes portfolio imbalances?
250. How do you communicate strategy retirement decisions to stakeholders?

### Strategy Capacity

251. How do you estimate the capacity of each strategy?
252. What happens when a strategy exceeds its capacity?
253. How do you detect when strategy performance is degrading due to capacity constraints?
254. What is your strategy for managing capacity across multiple strategies?
255. How do you handle strategies that have different capacity in different market conditions?
256. What happens when total strategy capacity exceeds available capital?
257. How do you prioritize capital allocation when capacity is constrained?
258. What is your process for increasing strategy capacity?
259. How do you handle strategies that have capacity constraints you didn't anticipate?
260. What happens when capacity estimation is systematically wrong?

### Strategy Correlation

261. How do you measure correlation between strategies?
262. What happens when strategies that should be uncorrelated become correlated?
263. How do you handle strategies that are correlated in tail events?
264. What is your strategy for managing portfolio-level correlation risk?
265. How do you detect when correlation structure is changing?
266. What happens when correlation spikes during market stress?
267. How do you handle strategies that are negatively correlated (hedging)?
268. What is your process for rebalancing when correlations change?
269. How do you model correlation under different market regimes?
270. What happens when correlation estimation is unreliable?
