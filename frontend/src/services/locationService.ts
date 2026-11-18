export interface LocationCoordinates {
    latitude: number;
    longitude: number;
    accuracy: number;
}

export function getCurrentLocation(): Promise<LocationCoordinates> {
    return new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
            reject({
                code: "UNSUPPORTED",
                message: "Geolocation is not supported by this browser.",
            });

            return;
        }

        navigator.geolocation.getCurrentPosition(
            (position) => {
                const { latitude, longitude, accuracy } = position.coords;

                resolve({
                    latitude,
                    longitude,
                    accuracy,
                });
            },

            (error) => {
                switch (error.code) {
                    case error.PERMISSION_DENIED:
                        reject({
                            code: "PERMISSION_DENIED",
                            message:
                                "Location permission was denied. Please allow location access.",
                        });
                        break;

                    case error.POSITION_UNAVAILABLE:
                        reject({
                            code: "POSITION_UNAVAILABLE",
                            message:
                                "Your current location could not be determined.",
                        });
                        break;

                    case error.TIMEOUT:
                        reject({
                            code: "TIMEOUT",
                            message:
                                "Location request timed out. Please try again.",
                        });
                        break;

                    default:
                        reject({
                            code: "UNKNOWN",
                            message:
                                "An unknown error occurred while retrieving your location.",
                        });
                }
            },

            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 60000,
            }
        );
    });
}