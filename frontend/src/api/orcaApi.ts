import type {
  ApiErrorResponse,
  IntelligenceDecision,
  TripAnalysisRequest,
} from "../types/orca";

const DEFAULT_API_BASE_URL =
  "http://127.0.0.1:8000/api/v1";

const REQUEST_TIMEOUT_MS = 30_000;

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL
).replace(/\/+$/, "");


export class OrcaApiError extends Error {
  readonly status: number;
  readonly details: ApiErrorResponse | null;

  constructor(
    message: string,
    status: number,
    details: ApiErrorResponse | null = null,
  ) {
    super(message);

    this.name = "OrcaApiError";
    this.status = status;
    this.details = details;
  }
}


function getErrorMessage(
  errorResponse: ApiErrorResponse | null,
): string {
  if (!errorResponse) {
    return "ORCA could not process the request.";
  }

  if (typeof errorResponse.detail === "string") {
    return errorResponse.detail;
  }

  if (Array.isArray(errorResponse.detail)) {
    return errorResponse.detail
      .map((error) => {
        const field = error.loc
          .filter((part) => part !== "body")
          .join(".");

        return field
          ? `${field}: ${error.msg}`
          : error.msg;
      })
      .join(" ");
  }

  return "ORCA could not process the request.";
}


async function parseErrorResponse(
  response: Response,
): Promise<ApiErrorResponse | null> {
  try {
    return (await response.json()) as ApiErrorResponse;
  } catch {
    return null;
  }
}


async function request<TResponse>(
  path: string,
  options: RequestInit,
): Promise<TResponse> {
  const controller = new AbortController();

  const timeoutId = window.setTimeout(
    () => controller.abort(),
    REQUEST_TIMEOUT_MS,
  );

  try {
    const response = await fetch(
      `${API_BASE_URL}${path}`,
      {
        ...options,
        signal: controller.signal,
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
          ...options.headers,
        },
      },
    );

    if (!response.ok) {
      const errorResponse = await parseErrorResponse(response);

      throw new OrcaApiError(
        getErrorMessage(errorResponse),
        response.status,
        errorResponse,
      );
    }

    return (await response.json()) as TResponse;
  } catch (error) {
    if (error instanceof OrcaApiError) {
      throw error;
    }

    if (
      error instanceof DOMException &&
      error.name === "AbortError"
    ) {
      throw new OrcaApiError(
        "The ORCA request timed out. Please try again.",
        408,
      );
    }

    throw new OrcaApiError(
      "Unable to connect to ORCA. Confirm that the backend is running.",
      0,
    );
  } finally {
    window.clearTimeout(timeoutId);
  }
}


export async function analyzeTrip(
  tripRequest: TripAnalysisRequest,
): Promise<IntelligenceDecision> {
  return request<IntelligenceDecision>(
    "/trips/analyze",
    {
      method: "POST",
      body: JSON.stringify(tripRequest),
    },
  );
}