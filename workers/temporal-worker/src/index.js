const taskQueue = process.env.TEMPORAL_TASK_QUEUE || "tutu-phase1";
const host = process.env.TEMPORAL_HOST || "localhost:7233";

console.log(`Temporal worker scaffold ready.`);
console.log(`Connect worker to ${host} on queue ${taskQueue}.`);
console.log(`Implement workflows/activities in Phase 2.`);
