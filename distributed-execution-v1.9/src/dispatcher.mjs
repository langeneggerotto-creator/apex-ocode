export class Dispatcher {
  constructor(workers = []) {
    this.workers = workers;
    this.index = 0;
  }

  nextWorker() {
    if (this.workers.length === 0) throw new Error('No workers available');
    const worker = this.workers[this.index % this.workers.length];
    this.index++;
    return worker;
  }

  async dispatch(plan) {
    const results = [];

    for (const step of plan.steps) {
      const worker = this.nextWorker();
      const result = await worker.run(step);
      results.push(result);

      if (!result.success) {
        return {
          success: false,
          failedStep: step,
          results
        };
      }
    }

    return {
      success: true,
      results
    };
  }
}
