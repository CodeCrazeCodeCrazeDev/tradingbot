# 1,000 CRITICAL QUESTIONS - PART 3

## SECTION 5: MACHINE LEARNING FAILURE MODES & CONCEPT DRIFT (Questions 271-340)

### Model Training

271. How do you detect when training data is not representative of future conditions?
272. What happens when training converges to a local minimum?
273. How do you handle training instability and divergence?
274. What is your strategy for handling class imbalance in training data?
275. How do you detect when training is overfitting to noise?
276. What happens when training requires more compute than available?
277. How do you handle training data that contains errors?
278. What is your strategy for handling missing features in training data?
279. How do you detect when training is memorizing rather than generalizing?
280. What happens when training produces models that are too complex to deploy?

### Model Validation

281. How do you validate that model performance generalizes to unseen data?
282. What happens when validation metrics disagree with each other?
283. How do you detect when validation is contaminated by data leakage?
284. What is your strategy for handling models that validate well but fail in production?
285. How do you validate model behavior under distribution shift?
286. What happens when validation data is not representative of production conditions?
287. How do you handle models that pass validation but have unacceptable latency?
288. What is your strategy for validating model robustness to input perturbations?
289. How do you detect when validation methodology is flawed?
290. What happens when models pass validation but have poor calibration?

### Model Deployment

291. How do you deploy models without disrupting live trading?
292. What happens when model deployment fails halfway through?
293. How do you handle models that require different infrastructure than existing models?
294. What is your strategy for A/B testing models in production?
295. How do you detect when a deployed model is behaving differently than in validation?
296. What happens when model deployment causes latency regressions?
297. How do you handle models that require warm-up data after deployment?
298. What is your strategy for coordinating model deployment with strategy deployment?
299. How do you rollback a model deployment that causes problems?
300. What happens when model deployment automation fails?

### Concept Drift

301. How do you detect when the relationship between features and targets has changed?
302. What happens when concept drift is gradual and hard to detect?
303. How do you distinguish between concept drift and model degradation?
304. What is your strategy for adapting models to concept drift?
305. How do you detect when concept drift is temporary vs. permanent?
306. What happens when concept drift affects some features but not others?
307. How do you handle concept drift that only manifests in tail events?
308. What is your strategy for detecting concept drift before it causes losses?
309. How do you handle concept drift in models that are expensive to retrain?
310. What happens when concept drift detection itself fails?

### Feature Engineering

311. How do you detect when features become stale or irrelevant?
312. What happens when feature computation fails for some inputs?
313. How do you handle features that have different distributions in training vs. production?
314. What is your strategy for handling features with missing values?
315. How do you detect when feature engineering introduces look-ahead bias?
316. What happens when features are computed incorrectly in production?
317. How do you handle features that are expensive to compute?
318. What is your strategy for versioning features and their transformations?
319. How do you detect when feature correlations change over time?
320. What happens when feature engineering creates unstable features?

### Model Monitoring

321. What metrics do you track for deployed models?
322. How do you detect when model predictions become unreliable?
323. What is your threshold for triggering model retraining?
324. How do you handle models that degrade slowly over time?
325. What happens when model monitoring infrastructure fails?
326. How do you detect when model outputs are systematically biased?
327. What is your strategy for monitoring model calibration over time?
328. How do you handle models that perform well on average but fail in specific conditions?
329. What happens when model monitoring generates too many false alarms?
330. How do you detect when model monitoring metrics are misleading?

### Model Failure Modes

331. What happens when a model produces NaN or infinite outputs?
332. How do you handle models that produce outputs outside expected ranges?
333. What is your strategy for handling model timeouts?
334. How do you detect when models are producing adversarial outputs?
335. What happens when model dependencies (libraries, weights) become corrupted?
336. How do you handle models that fail silently without raising errors?
337. What is your strategy for handling models that are sensitive to input order?
338. How do you detect when models are being exploited by adversaries?
339. What happens when model failure cascades to other system components?
340. How do you recover from model failures without manual intervention?

---

## SECTION 6: REINFORCEMENT LEARNING REWARD INTEGRITY (Questions 341-400)

### Reward Design

341. How do you ensure your reward function captures what you actually want to optimize?
342. What happens when the reward function has unintended optima?
343. How do you detect when the agent is gaming the reward function?
344. What is your strategy for handling sparse rewards?
345. How do you balance short-term and long-term rewards?
346. What happens when reward signals are delayed?
347. How do you handle rewards that are noisy or stochastic?
348. What is your strategy for reward shaping without introducing bias?
349. How do you detect when reward function changes cause behavioral changes?
350. What happens when the reward function conflicts with risk constraints?

### Reward Integrity

351. How do you ensure reward signals are not corrupted?
352. What happens when reward computation has bugs?
353. How do you detect when reward signals are being manipulated?
354. What is your strategy for validating reward signal accuracy?
355. How do you handle rewards that depend on external data that might be wrong?
356. What happens when reward signals are inconsistent across episodes?
357. How do you detect when reward signals have systematic biases?
358. What is your strategy for auditing reward signal computation?
359. How do you handle rewards that are computed retrospectively?
360. What happens when reward signal latency affects learning?

### Policy Learning

361. How do you detect when policy learning is diverging?
362. What happens when the policy converges to a degenerate solution?
363. How do you handle policy learning instability?
364. What is your strategy for balancing exploration and exploitation?
365. How do you detect when the policy is stuck in a local optimum?
366. What happens when policy updates cause catastrophic forgetting?
367. How do you handle policies that are sensitive to hyperparameters?
368. What is your strategy for policy learning with limited data?
369. How do you detect when policy learning is overfitting to recent experience?
370. What happens when policy learning requires more compute than available?

### Environment Modeling

371. How do you ensure your environment model is accurate?
372. What happens when the environment model diverges from reality?
373. How do you detect when environment dynamics have changed?
374. What is your strategy for handling environment non-stationarity?
375. How do you handle environment models that are computationally expensive?
376. What happens when environment simulation has bugs?
377. How do you detect when environment modeling introduces biases?
378. What is your strategy for validating environment model accuracy?
379. How do you handle environments with partial observability?
380. What happens when environment complexity exceeds modeling capacity?

### Safety Constraints

381. How do you enforce safety constraints during RL training?
382. What happens when the agent finds ways to violate safety constraints?
383. How do you detect when safety constraints are too restrictive?
384. What is your strategy for handling safety constraints that conflict with rewards?
385. How do you ensure safety constraints are maintained during deployment?
386. What happens when safety constraint enforcement fails?
387. How do you handle safety constraints that depend on external state?
388. What is your strategy for updating safety constraints without retraining?
389. How do you detect when safety constraints are being circumvented?
390. What happens when safety constraints cause the agent to be non-competitive?

### RL Deployment

391. How do you deploy RL agents without causing market disruption?
392. What happens when deployed RL agents behave differently than in training?
393. How do you handle RL agents that require online learning in production?
394. What is your strategy for monitoring RL agent behavior in production?
395. How do you detect when RL agents are making systematically bad decisions?
396. What happens when RL agent deployment causes latency issues?
397. How do you handle RL agents that interact with each other?
398. What is your strategy for rolling back RL agent deployments?
399. How do you detect when RL agents are being exploited by adversaries?
400. What happens when RL agent failure modes are different from supervised models?

---

## SECTION 7: RISK MANAGEMENT, DRAWDOWN CONTROL & TAIL RISK (Questions 401-470)

### Position Risk

401. How do you calculate position risk in real-time?
402. What happens when position risk calculation has errors?
403. How do you handle positions that exceed risk limits?
404. What is your strategy for handling positions in illiquid instruments?
405. How do you detect when position risk is underestimated?
406. What happens when position risk changes faster than you can respond?
407. How do you handle positions with non-linear risk profiles (options)?
408. What is your strategy for handling positions with uncertain valuations?
409. How do you detect when position risk models are miscalibrated?
410. What happens when position risk limits are breached during market hours?

### Portfolio Risk

411. How do you calculate portfolio-level risk?
412. What happens when portfolio risk exceeds acceptable levels?
413. How do you handle portfolio risk that is concentrated in specific factors?
414. What is your strategy for managing portfolio risk across asset classes?
415. How do you detect when portfolio risk is correlated with market risk?
416. What happens when portfolio risk models fail during market stress?
417. How do you handle portfolio risk from positions you cannot easily exit?
418. What is your strategy for portfolio risk budgeting?
419. How do you detect when portfolio risk is hidden in correlations?
420. What happens when portfolio risk limits conflict with strategy requirements?

### Drawdown Control

421. What is your maximum acceptable drawdown?
422. How do you detect when drawdown is approaching critical levels?
423. What happens when drawdown exceeds your maximum threshold?
424. What is your strategy for reducing exposure during drawdowns?
425. How do you handle drawdowns that occur faster than you can respond?
426. What happens when drawdown control mechanisms fail?
427. How do you distinguish between temporary drawdowns and strategy failure?
428. What is your strategy for recovering from significant drawdowns?
429. How do you handle drawdowns that are caused by external factors?
430. What happens when drawdown control causes you to miss recovery?

### Tail Risk

431. How do you model tail risk in your portfolio?
432. What happens when tail events exceed your model assumptions?
433. How do you hedge against tail risk?
434. What is your strategy for handling tail risk that cannot be hedged?
435. How do you detect when tail risk is increasing?
436. What happens when tail risk hedges fail to perform?
437. How do you handle tail risk from correlated positions?
438. What is your strategy for tail risk during market dislocations?
439. How do you detect when tail risk models are underestimating risk?
440. What happens when tail events occur more frequently than modeled?

### Leverage

441. What is your maximum leverage, and how is it enforced?
442. How do you detect when leverage is approaching limits?
443. What happens when leverage limits are breached?
444. What is your strategy for managing leverage across strategies?
445. How do you handle leverage requirements that change during market stress?
446. What happens when leverage calculation has errors?
447. How do you handle leverage from instruments with embedded leverage?
448. What is your strategy for deleveraging during market stress?
449. How do you detect when leverage is hidden in complex instruments?
450. What happens when forced deleveraging causes additional losses?

### Liquidity Risk

451. How do you measure liquidity risk in your portfolio?
452. What happens when liquidity dries up in positions you hold?
453. How do you handle positions that become illiquid unexpectedly?
454. What is your strategy for managing liquidity risk during market stress?
455. How do you detect when liquidity risk is increasing?
456. What happens when liquidity risk models fail?
457. How do you handle liquidity risk from large positions?
458. What is your strategy for maintaining liquidity buffers?
459. How do you detect when liquidity conditions are deteriorating?
460. What happens when liquidity risk causes forced selling?

### Counterparty Risk

461. How do you assess counterparty risk for each broker/exchange?
462. What happens when a counterparty fails?
463. How do you handle counterparty risk concentration?
464. What is your strategy for managing counterparty risk across venues?
465. How do you detect when counterparty risk is increasing?
466. What happens when counterparty risk materializes during market stress?
467. How do you handle counterparty risk from margin requirements?
468. What is your strategy for counterparty risk in OTC instruments?
469. How do you detect when counterparty risk is hidden in complex arrangements?
470. What happens when counterparty risk causes cascading failures?
