export class ApiError extends Error {
  status: number;
  code: string;
  safeMessage: string;

  constructor(status: number, code: string, safeMessage: string) {
    super(safeMessage);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.safeMessage = safeMessage;
  }
}
