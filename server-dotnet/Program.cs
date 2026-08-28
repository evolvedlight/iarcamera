using System.Text.Json.Serialization;
using System.Text.RegularExpressions;
using Microsoft.Extensions.Caching.Memory;

namespace CameraServer;

public class Program
{
    public static async Task<int> Main(string[] args)
    {
        // 1. Resolve root directory containing photos and web
        var rootDir = Directory.GetCurrentDirectory();
        if (!Directory.Exists(Path.Combine(rootDir, "photos")) && !Directory.Exists(Path.Combine(rootDir, "web")))
        {
            var exeDir = AppContext.BaseDirectory;
            var current = new DirectoryInfo(exeDir);
            while (current != null)
            {
                if (Directory.Exists(Path.Combine(current.FullName, "photos")) || Directory.Exists(Path.Combine(current.FullName, "web")))
                {
                    rootDir = current.FullName;
                    break;
                }
                current = current.Parent;
            }
        }

        string photosDir = Path.Combine(rootDir, "photos");
        string webDir = Path.Combine(rootDir, "web");

        Console.WriteLine("============================================================");
        Console.WriteLine("  IAR Camera Timelapse UI Server (.NET 10.0 - Optimized)");
        Console.WriteLine($"  Root directory: {rootDir}");
        Console.WriteLine("============================================================");

        // 2. Self-healing port selection loop
        int port = 8000;
        WebApplication? app = null;
        bool started = false;

        while (!started && port < 8050)
        {
            var builder = WebApplication.CreateBuilder(args);
            
            // Limit logging noise for performance and clean console output
            builder.Logging.ClearProviders();
            builder.Logging.AddConsole();
            builder.Logging.SetMinimumLevel(LogLevel.Warning);

            // Configure memory cache with 1GB limit (for caching image bytes and API metadata)
            builder.Services.AddMemoryCache(options =>
            {
                options.SizeLimit = 1024 * 1024 * 1024; // 1 GB size limit
            });

            builder.WebHost.ConfigureKestrel(options =>
            {
                options.ListenLocalhost(port);
            });

            var tempApp = builder.Build();

            // Setup endpoints
            ConfigureRoutes(tempApp, photosDir, webDir, rootDir);

            try
            {
                await tempApp.StartAsync();
                app = tempApp;
                started = true;
            }
            catch (Exception)
            {
                Console.ForegroundColor = ConsoleColor.Gray;
                Console.WriteLine($"Port {port} is in use or locked. Trying next port...");
                Console.ResetColor();
                await tempApp.DisposeAsync();
                port++;
            }
        }

        if (!started || app == null)
        {
            Console.ForegroundColor = ConsoleColor.Red;
            Console.WriteLine("Failed to start server on any port between 8000 and 8050. Check permissions.");
            Console.ResetColor();
            return 1;
        }

        Console.ForegroundColor = ConsoleColor.Cyan;
        Console.WriteLine("============================================================");
        Console.ForegroundColor = ConsoleColor.Green;
        Console.WriteLine("  IAR Camera Timelapse UI Server is running!");
        Console.ForegroundColor = ConsoleColor.White;
        Console.WriteLine("  Open your browser and navigate to:");
        Console.ForegroundColor = ConsoleColor.Yellow;
        Console.WriteLine($"      http://localhost:{port}/");
        Console.ForegroundColor = ConsoleColor.Gray;
        Console.WriteLine("  Press Ctrl+C in this terminal to stop the server.");
        Console.ForegroundColor = ConsoleColor.Cyan;
        Console.WriteLine("============================================================");
        Console.ResetColor();

        await app.WaitForShutdownAsync();
        return 0;
    }

    private static void ConfigureRoutes(WebApplication app, string photosDir, string webDir, string rootDir)
    {
        // Route API endpoints
        app.MapGet("/api/dates", (HttpContext context, IMemoryCache cache) =>
        {
            context.Response.Headers.AccessControlAllowOrigin = "*";
            context.Response.Headers.CacheControl = "public, max-age=10"; // Short cache for dates

            const string cacheKey = "api:dates";
            if (cache.TryGetValue(cacheKey, out List<DateFolderItem>? cachedDates) && cachedDates != null)
            {
                return Results.Json(cachedDates);
            }

            var dateFolders = new List<DateFolderItem>();
            if (Directory.Exists(photosDir))
            {
                try
                {
                    var dirs = Directory.GetDirectories(photosDir);
                    foreach (var dir in dirs)
                    {
                        var dirName = Path.GetFileName(dir);
                        if (Regex.IsMatch(dirName, @"^\d{4}-\d{2}-\d{2}$"))
                        {
                            int imgCount = Directory.EnumerateFiles(dir, "*.jpg").Count();
                            if (imgCount > 0)
                            {
                                dateFolders.Add(new DateFolderItem(dirName, imgCount));
                            }
                        }
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Error scanning date directories: {ex.Message}");
                }
            }

            dateFolders = dateFolders.OrderByDescending(d => d.Date).ToList();

            var cacheOptions = new MemoryCacheEntryOptions()
                .SetAbsoluteExpiration(TimeSpan.FromSeconds(10))
                .SetSize(1); // Small size unit for metadata

            cache.Set(cacheKey, dateFolders, cacheOptions);

            return Results.Json(dateFolders);
        });

        app.MapGet("/api/photos", (string? days, string? dates, HttpContext context, IMemoryCache cache) =>
        {
            context.Response.Headers.AccessControlAllowOrigin = "*";
            context.Response.Headers.CacheControl = "public, max-age=10"; // Short cache for photo list

            string daysParam = days ?? "3";
            string? datesParam = dates;

            string cacheKey = $"api:photos:days={daysParam}:dates={datesParam ?? ""}";
            if (cache.TryGetValue(cacheKey, out List<PhotoItem>? cachedPhotos) && cachedPhotos != null)
            {
                return Results.Json(cachedPhotos);
            }

            var allDates = new List<string>();
            if (Directory.Exists(photosDir))
            {
                try
                {
                    var dirs = Directory.GetDirectories(photosDir);
                    foreach (var dir in dirs)
                    {
                        var dirName = Path.GetFileName(dir);
                        if (Regex.IsMatch(dirName, @"^\d{4}-\d{2}-\d{2}$"))
                        {
                            allDates.Add(dirName);
                        }
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Error scanning photos directories: {ex.Message}");
                }
            }

            allDates = allDates.OrderByDescending(d => d).ToList();

            var targetDates = new List<string>();
            if (!string.IsNullOrEmpty(datesParam))
            {
                targetDates = datesParam.Split(',')
                                        .Select(d => d.Trim())
                                        .Where(d => !string.IsNullOrEmpty(d))
                                        .ToList();
            }
            else
            {
                if (daysParam == "all")
                {
                    targetDates = allDates;
                }
                else
                {
                    if (!int.TryParse(daysParam, out int numDays))
                    {
                        numDays = 3;
                    }
                    targetDates = allDates.Take(numDays).ToList();
                }
            }

            var photos = new List<PhotoItem>();
            foreach (var date in targetDates)
            {
                string dateDir = Path.Combine(photosDir, date);
                if (Directory.Exists(dateDir))
                {
                    try
                    {
                        var files = Directory.GetFiles(dateDir, "*.jpg");
                        foreach (var file in files)
                        {
                            string filename = Path.GetFileName(file);
                            string filenameWithoutExt = Path.GetFileNameWithoutExtension(filename);
                            var match = Regex.Match(filenameWithoutExt, @"^(\d{4}-\d{2}-\d{2})_(\d{2})-(\d{2})-(\d{2})$");
                            string formattedTime = "";
                            if (match.Success)
                            {
                                formattedTime = $"{match.Groups[1].Value} {match.Groups[2].Value}:{match.Groups[3].Value}:{match.Groups[4].Value}";
                            }
                            string webPath = $"photos/{date}/{filename}";
                            photos.Add(new PhotoItem(webPath, formattedTime, date, filename));
                        }
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine($"Error reading files in {dateDir}: {ex.Message}");
                    }
                }
            }

            // Sort ascending
            photos = photos.OrderBy(p => p.Time).ToList();

            // Automatic Subsampling
            int maxPhotos = 1200;
            int totalCount = photos.Count;
            if (totalCount > maxPhotos)
            {
                int step = (int)Math.Ceiling((double)totalCount / maxPhotos);
                var subsampled = new List<PhotoItem>();
                for (int i = 0; i < totalCount; i += step)
                {
                    subsampled.Add(photos[i]);
                }
                if (subsampled.Count > 0 && subsampled[^1].Path != photos[^1].Path)
                {
                    subsampled.Add(photos[^1]);
                }
                photos = subsampled;
                Console.ForegroundColor = ConsoleColor.Gray;
                Console.WriteLine($"Subsampled {totalCount} photos down to {photos.Count} frames (step: {step})");
                Console.ResetColor();
            }

            var cacheOptions = new MemoryCacheEntryOptions()
                .SetAbsoluteExpiration(TimeSpan.FromSeconds(10))
                .SetSize(1); // Small size unit for metadata

            cache.Set(cacheKey, photos, cacheOptions);

            return Results.Json(photos);
        });

        // Serve static files with memory cache for images
        app.MapGet("{*path}", async (string? path, HttpContext context, IMemoryCache cache) =>
        {
            path = path ?? "";
            path = path.TrimStart('/');
            if (path == "")
            {
                path = "web/index.html";
            }

            // Try to find the file
            string filePath = Path.Combine(rootDir, path.Replace('/', Path.DirectorySeparatorChar));

            // Fallback logic matching server.ps1
            if (!File.Exists(filePath) && !path.StartsWith("photos/", StringComparison.OrdinalIgnoreCase))
            {
                string webPath = Path.Combine(rootDir, "web", path.Replace('/', Path.DirectorySeparatorChar));
                if (File.Exists(webPath))
                {
                    filePath = webPath;
                }
            }

            if (File.Exists(filePath))
            {
                string contentType = GetContentType(filePath);
                context.Response.Headers.AccessControlAllowOrigin = "*";

                // Optimization: Detect if request is for a photo
                bool isPhoto = path.StartsWith("photos/", StringComparison.OrdinalIgnoreCase) && 
                               (filePath.EndsWith(".jpg", StringComparison.OrdinalIgnoreCase) || 
                                filePath.EndsWith(".jpeg", StringComparison.OrdinalIgnoreCase));

                if (isPhoto)
                {
                    // Aggressive client caching: 1 year, immutable.
                    // This tells the browser to load it directly from its memory/disk cache 
                    // without making any network request.
                    context.Response.Headers.CacheControl = "public, max-age=31536000, immutable";

                    string cacheKey = $"file:{filePath.ToLowerInvariant()}";
                    if (cache.TryGetValue(cacheKey, out byte[]? cachedBytes) && cachedBytes != null)
                    {
                        return Results.Bytes(cachedBytes, contentType);
                    }

                    try
                    {
                        // Async read file from disk
                        byte[] fileBytes = await File.ReadAllBytesAsync(filePath);
                        
                        var cacheEntryOptions = new MemoryCacheEntryOptions()
                            .SetSize(fileBytes.Length) // Track size in bytes for the 1GB limit
                            .SetSlidingExpiration(TimeSpan.FromMinutes(20)) // Evict if inactive for 20m
                            .SetAbsoluteExpiration(TimeSpan.FromHours(2));  // Max cache duration 2h

                        cache.Set(cacheKey, fileBytes, cacheEntryOptions);
                        
                        return Results.Bytes(fileBytes, contentType);
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine($"Error caching file {filePath}: {ex.Message}");
                    }
                }

                // Cache static assets (CSS, JS, HTML) for 1 hour to prevent redundant requests
                if (filePath.EndsWith(".js") || filePath.EndsWith(".css") || filePath.EndsWith(".html"))
                {
                    context.Response.Headers.CacheControl = "public, max-age=3600";
                }

                var lastModified = File.GetLastWriteTimeUtc(filePath);
                return Results.File(filePath, contentType, lastModified: lastModified);
            }

            context.Response.Headers.AccessControlAllowOrigin = "*";
            return Results.NotFound("404 Not Found");
        });
    }

    private static string GetContentType(string filePath)
    {
        string ext = Path.GetExtension(filePath).ToLowerInvariant();
        return ext switch
        {
            ".html" => "text/html; charset=utf-8",
            ".css" => "text/css; charset=utf-8",
            ".js" => "application/javascript; charset=utf-8",
            ".jpg" or ".jpeg" => "image/jpeg",
            ".png" => "image/png",
            ".gif" => "image/gif",
            ".json" => "application/json; charset=utf-8",
            ".svg" => "image/svg+xml; charset=utf-8",
            _ => "application/octet-stream"
        };
    }
}

public record DateFolderItem(
    [property: JsonPropertyName("date")] string Date,
    [property: JsonPropertyName("count")] int Count
);

public record PhotoItem(
    [property: JsonPropertyName("path")] string Path,
    [property: JsonPropertyName("time")] string Time,
    [property: JsonPropertyName("date")] string Date,
    [property: JsonPropertyName("filename")] string Filename
);
