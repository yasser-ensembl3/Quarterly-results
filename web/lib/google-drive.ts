import { google, drive_v3 } from 'googleapis';

export interface DriveFile {
  id: string;
  name: string;
  mimeType: string;
}

export interface SourceFile {
  id: string;
  name: string;
  mimeType: string;
  type: 'pdf' | 'audio' | 'video' | 'image' | 'document' | 'other';
  viewUrl: string;
  downloadUrl: string;
}

export interface QuarterFolder {
  id: string;
  name: string;
  companies: {
    name: string;
    folderId: string;
    jsonFileId: string | null;
  }[];
}

let driveClient: drive_v3.Drive | null = null;

function getDriveClient(): drive_v3.Drive {
  if (driveClient) return driveClient;

  // OAuth2 with refresh token
  const clientId = process.env.GOOGLE_CLIENT_ID;
  const clientSecret = process.env.GOOGLE_CLIENT_SECRET;
  const refreshToken = process.env.GOOGLE_REFRESH_TOKEN;

  if (!clientId || !clientSecret || !refreshToken) {
    throw new Error('Google OAuth2 credentials not configured (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN)');
  }

  const oauth2Client = new google.auth.OAuth2(clientId, clientSecret);
  oauth2Client.setCredentials({ refresh_token: refreshToken });

  driveClient = google.drive({ version: 'v3', auth: oauth2Client });
  return driveClient;
}

export async function listFolderContents(folderId: string): Promise<DriveFile[]> {
  const drive = getDriveClient();
  const files: DriveFile[] = [];
  let pageToken: string | undefined;

  do {
    const response = await drive.files.list({
      q: `'${folderId}' in parents and trashed = false`,
      fields: 'nextPageToken, files(id, name, mimeType)',
      pageToken,
      orderBy: 'name',
    });

    for (const file of response.data.files || []) {
      if (file.id && file.name && file.mimeType) {
        files.push({
          id: file.id,
          name: file.name,
          mimeType: file.mimeType,
        });
      }
    }

    pageToken = response.data.nextPageToken || undefined;
  } while (pageToken);

  return files;
}

export async function fetchFileContent<T>(fileId: string): Promise<T> {
  const drive = getDriveClient();

  const response = await drive.files.get(
    { fileId, alt: 'media' },
    { responseType: 'text' }
  );

  return JSON.parse(response.data as string) as T;
}

export async function listQuarterFolders(): Promise<DriveFile[]> {
  const rootFolderId = process.env.GDRIVE_ROOT_FOLDER_ID;
  if (!rootFolderId) {
    throw new Error('GDRIVE_ROOT_FOLDER_ID is not configured');
  }

  const contents = await listFolderContents(rootFolderId);
  return contents
    .filter(f => f.mimeType === 'application/vnd.google-apps.folder')
    .sort((a, b) => b.name.localeCompare(a.name)); // Most recent first
}

export async function listCompanyFolders(quarterFolderId: string): Promise<DriveFile[]> {
  const contents = await listFolderContents(quarterFolderId);
  return contents.filter(f => f.mimeType === 'application/vnd.google-apps.folder');
}

export async function findJsonFile(companyFolderId: string): Promise<DriveFile | null> {
  const contents = await listFolderContents(companyFolderId);
  const jsonFile = contents.find(
    f => f.name.endsWith('.json') && !f.name.startsWith('.')
  );
  return jsonFile || null;
}

export async function buildQuarterStructure(quarterFolderId: string, quarterName: string): Promise<QuarterFolder> {
  const companyFolders = await listCompanyFolders(quarterFolderId);

  const companies = await Promise.all(
    companyFolders.map(async (folder) => {
      const jsonFile = await findJsonFile(folder.id);
      return {
        name: folder.name,
        folderId: folder.id,
        jsonFileId: jsonFile?.id || null,
      };
    })
  );

  return {
    id: quarterFolderId,
    name: quarterName,
    companies: companies.filter(c => c.jsonFileId !== null),
  };
}

export async function getLatestQuarterStructure(): Promise<QuarterFolder | null> {
  const quarters = await listQuarterFolders();
  if (quarters.length === 0) return null;

  const latestQuarter = quarters[0];
  return buildQuarterStructure(latestQuarter.id, latestQuarter.name);
}

export function isGoogleDriveConfigured(): boolean {
  return !!(
    process.env.GOOGLE_CLIENT_ID &&
    process.env.GOOGLE_CLIENT_SECRET &&
    process.env.GOOGLE_REFRESH_TOKEN &&
    process.env.GDRIVE_ROOT_FOLDER_ID
  );
}

function getFileType(mimeType: string, name: string): SourceFile['type'] {
  if (mimeType === 'application/pdf' || name.endsWith('.pdf')) return 'pdf';
  if (mimeType.startsWith('audio/') || name.match(/\.(mp3|wav|m4a|ogg)$/i)) return 'audio';
  if (mimeType.startsWith('video/') || name.match(/\.(mp4|mov|avi|mkv)$/i)) return 'video';
  if (mimeType.startsWith('image/') || name.match(/\.(jpg|jpeg|png|gif|webp)$/i)) return 'image';
  if (mimeType.includes('document') || mimeType.includes('word') || name.match(/\.(doc|docx|txt)$/i)) return 'document';
  return 'other';
}

export async function getCompanySourceFiles(ticker: string): Promise<SourceFile[]> {
  const quarterStructure = await getLatestQuarterStructure();
  if (!quarterStructure) return [];

  // Find company folder
  const TICKER_TO_FOLDER: Record<string, string[]> = {
    AMZN: ['amazon'],
    COIN: ['coinbase'],
    SHOP: ['shopify'],
    NVDA: ['nvidia', 'nvdia'],
    EBAY: ['ebay'],
    ETSY: ['etsy'],
    W: ['wayfair'],
    YETI: ['yeti'],
    FIGS: ['figs'],
    LVMH: ['lvmh'],
    CSI: ['constellation'],
    CRCL: ['circle'],
  };

  const matchingNames = TICKER_TO_FOLDER[ticker.toUpperCase()] || [ticker.toLowerCase()];
  const company = quarterStructure.companies.find(c =>
    matchingNames.some(match => c.name.toLowerCase().includes(match))
  );

  if (!company) return [];

  // Get all files in the folder
  const allFiles = await listFolderContents(company.folderId);

  // Filter out generated files (JSON, MD) and keep source files
  const sourceFiles = allFiles
    .filter(f => !f.name.endsWith('.json') && !f.name.endsWith('.md'))
    .filter(f => f.mimeType !== 'application/vnd.google-apps.folder')
    .map(f => ({
      id: f.id,
      name: f.name,
      mimeType: f.mimeType,
      type: getFileType(f.mimeType, f.name),
      viewUrl: `https://drive.google.com/file/d/${f.id}/view`,
      downloadUrl: `https://drive.google.com/uc?export=download&id=${f.id}`,
    }));

  return sourceFiles;
}
