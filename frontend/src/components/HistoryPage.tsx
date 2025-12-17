import React, { useState, useEffect } from 'react';
import {
  Box, Container, Typography, Paper, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Chip, Button, Tabs, Tab, CircularProgress, IconButton,
  Dialog, DialogTitle, DialogContent, DialogActions, Grid, Card, CardContent
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import DownloadIcon from '@mui/icons-material/Download';
import VisibilityIcon from '@mui/icons-material/Visibility';
import RefreshIcon from '@mui/icons-material/Refresh';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CancelIcon from '@mui/icons-material/Cancel';
import PendingIcon from '@mui/icons-material/Pending';
import { historyApi } from '../services/historyApi';
import './HistoryPage.css';

interface HistoryPageProps {
  onBack: () => void;
}

interface Application {
  id: string;
  customer_name: string;
  requested_amount: number;
  approved_amount?: number;
  tenure: number;
  interest_rate: number;
  emi?: number;
  status: string;
  credit_score?: number;
  sanction_letter_url?: string;
  created_at: string;
  updated_at: string;
}

interface SanctionLetter {
  id: string;
  customer_name: string;
  loan_amount: number;
  tenure: number;
  interest_rate: number;
  emi: number;
  filename: string;
  download_url: string;
  generated_at: string;
  downloaded_count: number;
}

interface Statistics {
  total_applications: number;
  approved: number;
  rejected: number;
  pending: number;
  approval_rate: number;
  total_sanctioned_amount: number;
  total_sanction_letters: number;
}

const HistoryPage: React.FC<HistoryPageProps> = ({ onBack }) => {
  const [tabValue, setTabValue] = useState(0);
  const [applications, setApplications] = useState<Application[]>([]);
  const [sanctionLetters, setSanctionLetters] = useState<SanctionLetter[]>([]);
  const [statistics, setStatistics] = useState<Statistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedApp, setSelectedApp] = useState<Application | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [appsRes, lettersRes, statsRes] = await Promise.all([
        historyApi.getApplications(),
        historyApi.getSanctionLetters(),
        historyApi.getStatistics()
      ]);
      
      if (appsRes.success) setApplications(appsRes.applications || []);
      if (lettersRes.success) setSanctionLetters(lettersRes.sanction_letters || []);
      if (statsRes.success) setStatistics(statsRes.statistics);
    } catch (error) {
      console.error('Error fetching history:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const getStatusChip = (status: string) => {
    const statusConfig: Record<string, { color: 'success' | 'error' | 'warning' | 'info'; icon: React.ReactNode }> = {
      approved: { color: 'success', icon: <CheckCircleIcon fontSize="small" /> },
      rejected: { color: 'error', icon: <CancelIcon fontSize="small" /> },
      completed: { color: 'success', icon: <CheckCircleIcon fontSize="small" /> },
      pending: { color: 'warning', icon: <PendingIcon fontSize="small" /> },
      in_progress: { color: 'info', icon: <PendingIcon fontSize="small" /> },
      verification_pending: { color: 'warning', icon: <PendingIcon fontSize="small" /> },
      underwriting: { color: 'info', icon: <PendingIcon fontSize="small" /> }
    };
    
    const config = statusConfig[status] || { color: 'info' as const, icon: null };
    return (
      <Chip 
        label={status.replace('_', ' ').toUpperCase()} 
        color={config.color} 
        size="small"
        icon={config.icon as React.ReactElement}
      />
    );
  };

  const formatCurrency = (amount: number) => `₹${amount?.toLocaleString('en-IN') || 0}`;
  const formatDate = (dateStr: string) => new Date(dateStr).toLocaleDateString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit'
  });

  const handleDownload = async (url: string, filename: string) => {
    try {
      const baseUrl = process.env.REACT_APP_API_URL || 'http://localhost:5001';
      window.open(`${baseUrl}${url}`, '_blank');
    } catch (error) {
      console.error('Download error:', error);
    }
  };

  return (
    <div className="history-page">
      <Box className="history-header">
        <Container maxWidth="lg">
          <Box display="flex" alignItems="center" gap={2}>
            <IconButton onClick={onBack} className="back-btn">
              <ArrowBackIcon />
            </IconButton>
            <Typography variant="h4" fontWeight={700}>Application History</Typography>
            <Box flex={1} />
            <Button startIcon={<RefreshIcon />} onClick={fetchData} variant="outlined">
              Refresh
            </Button>
          </Box>
        </Container>
      </Box>

      <Container maxWidth="lg" className="history-content">
        {/* Statistics Cards */}
        {statistics && (
          <Grid container spacing={3} className="stats-grid">
            <Grid size={{ xs: 6, md: 3 }}>
              <Card className="stat-card">
                <CardContent>
                  <Typography variant="h3">{statistics.total_applications}</Typography>
                  <Typography variant="body2">Total Applications</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid size={{ xs: 6, md: 3 }}>
              <Card className="stat-card approved">
                <CardContent>
                  <Typography variant="h3">{statistics.approved}</Typography>
                  <Typography variant="body2">Approved</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid size={{ xs: 6, md: 3 }}>
              <Card className="stat-card rejected">
                <CardContent>
                  <Typography variant="h3">{statistics.rejected}</Typography>
                  <Typography variant="body2">Rejected</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid size={{ xs: 6, md: 3 }}>
              <Card className="stat-card">
                <CardContent>
                  <Typography variant="h3">{statistics.approval_rate}%</Typography>
                  <Typography variant="body2">Approval Rate</Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        {/* Tabs */}
        <Paper className="tabs-paper">
          <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)}>
            <Tab label={`Applications (${applications.length})`} />
            <Tab label={`Sanction Letters (${sanctionLetters.length})`} />
          </Tabs>
        </Paper>

        {loading ? (
          <Box display="flex" justifyContent="center" py={8}>
            <CircularProgress />
          </Box>
        ) : (
          <>
            {/* Applications Tab */}
            {tabValue === 0 && (
              <TableContainer component={Paper} className="table-container">
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Application ID</TableCell>
                      <TableCell>Customer</TableCell>
                      <TableCell align="right">Amount</TableCell>
                      <TableCell align="center">Tenure</TableCell>
                      <TableCell align="center">Status</TableCell>
                      <TableCell>Date</TableCell>
                      <TableCell align="center">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {applications.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={7} align="center">
                          <Typography color="textSecondary" py={4}>
                            No applications yet. Start a new loan application!
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ) : (
                      applications.map((app) => (
                        <TableRow key={app.id} hover>
                          <TableCell><code>{app.id}</code></TableCell>
                          <TableCell>{app.customer_name}</TableCell>
                          <TableCell align="right">{formatCurrency(app.requested_amount)}</TableCell>
                          <TableCell align="center">{app.tenure} months</TableCell>
                          <TableCell align="center">{getStatusChip(app.status)}</TableCell>
                          <TableCell>{formatDate(app.created_at)}</TableCell>
                          <TableCell align="center">
                            <IconButton size="small" onClick={() => { setSelectedApp(app); setDetailsOpen(true); }}>
                              <VisibilityIcon />
                            </IconButton>
                            {app.sanction_letter_url && (
                              <IconButton size="small" color="primary" onClick={() => handleDownload(app.sanction_letter_url!, 'sanction_letter.pdf')}>
                                <DownloadIcon />
                              </IconButton>
                            )}
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            )}

            {/* Sanction Letters Tab */}
            {tabValue === 1 && (
              <TableContainer component={Paper} className="table-container">
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Letter ID</TableCell>
                      <TableCell>Customer</TableCell>
                      <TableCell align="right">Loan Amount</TableCell>
                      <TableCell align="right">EMI</TableCell>
                      <TableCell align="center">Downloads</TableCell>
                      <TableCell>Generated</TableCell>
                      <TableCell align="center">Action</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {sanctionLetters.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={7} align="center">
                          <Typography color="textSecondary" py={4}>
                            No sanction letters generated yet.
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ) : (
                      sanctionLetters.map((letter) => (
                        <TableRow key={letter.id} hover>
                          <TableCell><code>{letter.id}</code></TableCell>
                          <TableCell>{letter.customer_name}</TableCell>
                          <TableCell align="right">{formatCurrency(letter.loan_amount)}</TableCell>
                          <TableCell align="right">{formatCurrency(letter.emi)}</TableCell>
                          <TableCell align="center">
                            <Chip label={letter.downloaded_count} size="small" />
                          </TableCell>
                          <TableCell>{formatDate(letter.generated_at)}</TableCell>
                          <TableCell align="center">
                            <Button size="small" startIcon={<DownloadIcon />} onClick={() => handleDownload(letter.download_url, letter.filename)}>
                              Download
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </>
        )}
      </Container>

      {/* Details Dialog */}
      <Dialog open={detailsOpen} onClose={() => setDetailsOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Application Details</DialogTitle>
        <DialogContent dividers>
          {selectedApp && (
            <Grid container spacing={2}>
              <Grid size={6}><Typography variant="caption">Application ID</Typography><Typography fontWeight={600}>{selectedApp.id}</Typography></Grid>
              <Grid size={6}><Typography variant="caption">Status</Typography><Box>{getStatusChip(selectedApp.status)}</Box></Grid>
              <Grid size={6}><Typography variant="caption">Customer Name</Typography><Typography>{selectedApp.customer_name}</Typography></Grid>
              <Grid size={6}><Typography variant="caption">Credit Score</Typography><Typography>{selectedApp.credit_score || 'N/A'}</Typography></Grid>
              <Grid size={6}><Typography variant="caption">Requested Amount</Typography><Typography>{formatCurrency(selectedApp.requested_amount)}</Typography></Grid>
              <Grid size={6}><Typography variant="caption">Approved Amount</Typography><Typography>{selectedApp.approved_amount ? formatCurrency(selectedApp.approved_amount) : 'N/A'}</Typography></Grid>
              <Grid size={6}><Typography variant="caption">Tenure</Typography><Typography>{selectedApp.tenure} months</Typography></Grid>
              <Grid size={6}><Typography variant="caption">Interest Rate</Typography><Typography>{selectedApp.interest_rate}%</Typography></Grid>
              <Grid size={6}><Typography variant="caption">EMI</Typography><Typography>{selectedApp.emi ? formatCurrency(selectedApp.emi) : 'N/A'}</Typography></Grid>
              <Grid size={6}><Typography variant="caption">Applied On</Typography><Typography>{formatDate(selectedApp.created_at)}</Typography></Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailsOpen(false)}>Close</Button>
          {selectedApp?.sanction_letter_url && (
            <Button variant="contained" startIcon={<DownloadIcon />} onClick={() => handleDownload(selectedApp.sanction_letter_url!, 'sanction_letter.pdf')}>
              Download Letter
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </div>
  );
};

export default HistoryPage;
